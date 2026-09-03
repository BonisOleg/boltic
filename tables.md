# БОЛТіК° — tables.md (MVP)

Джерела: `boltiksitemap.pdf`, `каталог.docx`, рішення від 2026-07-22.

## Рішення

| Питання | Рішення |
|--------|---------|
| L3 | Немає окремого `Category` L3 — лист = `ProductGroup` |
| Category | Лише **L1–L2** (12 груп + підкатегорії з `каталог.docx`) |
| Ціна | `price` / опційно `sale_price` (роздріб); `party_price` грн/шт від `wholesale_from_qty`. Знімок у `OrderItem`. |
| Checkout | Гість: `Order.user` nullable; обовʼязкові імʼя + телефон; `access_token` для success |
| Документи PDP | `ProductDocument` у MVP |
| Купівля | Лише з `ProductSKU`; `qty ≥ min_party`, крок 1 |
| Наявність PDP | `in_stock` / `on_order` — обидва купуються; зняти з продажу = `is_active=False` |
| Оплата | `payment_status=pending` при place; LiqPay — пізніше |
| Логіка | Деталі в `business-logic.md` |

## Apps → моделі

| App | Моделі |
|-----|--------|
| `core` | `SiteSettings` |
| `catalog` | `Category`, `Brand`, `ProductGroup`, `ProductSKU`, `ProductImage`, `ProductDocument`, `Collection`, `FacetAttribute`, `FacetValue`, `SKUFacet` |
| `reviews` | `Review` |
| `cart` | `Cart`, `CartItem`, `WishlistItem` |
| `orders` | `Order`, `OrderItem` |
| `payments` | `PaymentTransaction` |
| `accounts` | `UserProfile` |
| `content` | `HomeBlock`, `Promotion`, `NewsPost`, `StaticPage`, `ContactBranch` |

## ER (ядро)

```
Category (L1–L2)
Brand ──────────→ ProductGroup ──1:N──→ ProductSKU
                       │                    │
              ProductImage / Document   CartItem / WishlistItem
              Review                    OrderItem (snapshot)
```

## URL → моделі (карта сайту)

| URL | Моделі |
|-----|--------|
| `/` | `HomeBlock`, `ProductGroup(is_top)` |
| `/katalog/`, `/katalog/{path}/` | `Category` + facets |
| `/tovar/{slug}/` | `ProductGroup`, `ProductSKU`, `ProductDocument`, `Review` |
| `/brendy/`, `/brendy/{slug}/` | `Brand` |
| `/pidbirka/{slug}/` | `Collection` |
| `/aktsiyi/` | `Promotion` |
| `/novyny/` | `NewsPost` |
| `/kontakty/` | `ContactBranch`, `SiteSettings` |
| сервісні сторінки | `StaticPage` |
| `/koshyk/`, `/bazhane/` | `Cart` / `WishlistItem` |
| `/oformlennya/` | `Order`, `OrderItem` |
| `/kabinet/` | `UserProfile`, `Order` |

---

## catalog

### Category
- `parent` FK self null (L1)
- `name`, `slug` (unique з parent)
- `path` indexed (`bolty-gvynty-stryazhni/bolty/`)
- `level` 1|2
- `sort_order`, `is_active`
- `seo_title`, `seo_description`
- **Constraint:** `unique(parent, slug)`, index(`path`)

### Brand
- `name`, `slug` unique, `logo?`, `description`, `is_active`

### ProductGroup (PDP `/tovar/{slug}/`)
- `category` FK → Category (L2)
- `brand` FK null
- `name`, `slug` unique
- `short_description`, `description`
- `standard`, `material`, `coating`, `industry` (nullable varchar)
- `diameter_min/max`, `length_min/max` (nullable decimal)
- `is_top`, `is_promo`, `is_active`
- `seo_title`, `seo_description`
- timestamps

### ProductSKU (рядок асортименту)
- `group` FK → ProductGroup
- `article` unique
- `name` — завжди з видимим розміром (`M6×50`)
- `size_label` — колонка «Розмір»
- `diameter`, `length`, `thread_pitch` nullable decimal
- `bore_d_mm`, `od_d_mm`, `width_b_mm` nullable decimal — підшипники: внутрішній d / зовнішній D / ширина B (мм); стандарт + ручне редагування в адмінці
- `head_width_mm` nullable decimal — автосаморізи: ширина головки; разом з `length` × `diameter` × `head_width_mm` (напр. 24×4,2×7,6); заповнення вручну
- `cell_a_mm`, `cell_b_mm` nullable — композитна сітка: ячейка A×B (мм); ціна на вітрині грн / м²
- `width_mm`, `thickness_mm` nullable — клинки: ширина і товщина (з `length`); арматура: `diameter` = D (мм), ціна грн / м.п.
- `volume_ml`, `manufacturer`, `application_zone` (internal|external|both), `pack_qty` — піни/клеї/герметики; `pack_qty` лише display; ціни грн/шт
- `strength_class` nullable
- `min_party` PositiveInt default 1 — мін. qty (крок 1)
- `wholesale_from_qty` nullable — поріг опту (шт)
- `stock_status` enum: `in_stock` | `on_order`
- `stock_qty` nullable int — ліміт у кошику; списання при place_order
- `price` Decimal(12,2) — база за шт
- `sale_price` nullable — акція лише в роздробі
- `price_includes_vat` bool default True
- `vat_rate` Decimal(5,2) default 20.00
- `party_price` nullable Decimal — опт грн/шт
- `is_active`, timestamps
- indexes: `(group, is_active)`, `(diameter, length)`, `(bore_d_mm, od_d_mm, width_b_mm)`

### ProductImage
- `group` FK, `image`, `alt`, `sort_order`, `is_primary`

### ProductDocument
- `group` FK, `title`, `file`, `sort_order`
- вкладка «Документи» на PDP

### Collection (`/pidbirka/{slug}/`)
- `title`, `slug`, `description`, `is_published`
- M2M → `ProductGroup`

### FacetAttribute / FacetValue / SKUFacet
- Attribute: `code` unique (`material`, `diametr`, `d`, `D`, `B`, …), `name`
- Value: FK attribute, `value`, `slug`; `unique(attribute, slug)`
- SKUFacet: M2M SKU ↔ Value  
- Фільтри: той самий URL категорії + `?code=slug`
- Підшипники: фасети `d` / `D` / `B` з полів `bore_d_mm` / `od_d_mm` / `width_b_mm` (команда `fill_bearing_dimensions` + `sync_facets`)
- Автосаморізи: фасети `dovzhyna` / `diametr` / `shiryna-golovky` з `length` / `diameter` / `head_width_mm` (ручне заповнення + `sync_facets`)
- Композит: арматура — `diametr` з `diameter`; сітка — `yacheyka-a` / `yacheyka-b`; клинки — `dovzhyna` / `shyryna` / `tovshchyna`
- Піни/клеї/герметики: `obiem` / `vyrobnyk` / `zona` з `volume_ml` / `manufacturer` / `application_zone`

---

## reviews

### Review
- `group` FK, `user` FK (обовʼязково — POST лише login)
- `rating` 1–5, `body`, `is_published`, `created_at`

---

## cart

### Cart
- `user` FK null, `session_key` null, `updated_at`
- хоча б одне з user/session_key

### CartItem
- `cart` FK, `sku` FK → ProductSKU
- `quantity`: `≥ min_party` (крок 1; див. `business-logic.md`)
- `unique(cart, sku)`

### WishlistItem
- `user` FK, `sku` FK, `unique(user, sku)`

---

## orders

### Order
- `number` unique (публічний)
- `access_token` UUID unique — доступ гостя до `/oformlennya/uspikh/{number}/`
- `user` FK **null** (гість)
- `status`: new | paid | processing | shipped | done | canceled
- `payment_status`: pending | paid | failed
- `customer_name`, `phone` (required), `email` optional (бажано для LiqPay)
- `shipping_method`, `shipping_address`
- `comment`, `total`
- знімок ПДВ на рівні позицій
- timestamps

### OrderItem
- `order` FK
- `sku` FK null SET_NULL
- snapshots: `article`, `name`, `size_label`, `unit_price`, `vat_rate`, `price_includes_vat`, `quantity`, `line_total`

---

## payments

### PaymentTransaction
- `order` FK → Order
- `provider`: `liqpay` (MVP)
- `status`: created | redirected | success | failure | refunded
- `amount` Decimal, `currency` default `UAH`
- `external_id` / LiqPay order id (indexed)
- `raw_request`, `raw_response` JSONField
- timestamps
- Ідемпотентний webhook; повторна оплата = новий рядок

URL: `/payments/liqpay/callback/`, `/payments/liqpay/result/`

---

## accounts

### UserProfile
- OneToOne → User
- `phone`, `company?`, `default_shipping_address?`

---

## content

### HomeBlock
- `key` unique (`hero`, `seo_text`, …), `title`, `body`, `is_active`, `sort_order`

### Promotion
- `title`, `slug`, `body`, `starts_at?`, `ends_at?`, `is_published`
- опційно M2M → ProductGroup / Collection

### NewsPost
- `title`, `slug`, `body`, `published_at`, `is_published`

### StaticPage
- `slug` unique (`oplata-i-dostavka`, `povernennya-ta-obmin`, …)
- `title`, `body`, `seo_*`

### ContactBranch
- `name`, `address`, `phone`, `email?`, `map_url?`, `sort_order`, `is_active`

---

## core

### SiteSettings (singleton)
- `site_name`, `phone`, `email`, `address`, `social_json?`
- `messenger_viber_url`, `messenger_whatsapp_url`, `messenger_telegram_url` — повні URL; на вітрині лише заповнені (`/kontakty/`, футер)

---

## Seed Category (L1 → L2)

1. **Болти, гвинти, стрижні** →  
   Болти з шестигранною головкою · Болти лемішні · Болти норійні · Болти меблеві ·  
   Гвинти з внутрішнім шестигранником · Гвинти потайні · Гвинти з прес-шайбою · Стрижні  
   *(плоскі «Болти»/«Гвинти» деактивовані після розфасовки імпорту)*  
2. **Гайки**, шайби, гровери → Гайки, Шайби, Гровери *(виправлено ГАКИ→ГАЙКИ)*  
3. Саморізи, шурупи → …  
4. Заклепки, шплінти, штифти → …  
5. Дюбелі, анкери → …  
6. Хомути, пластини, цвяхи → …  
7. Такелаж, троси, ланцюги → …  
8. Автокріплення → Болти, Саморізи, Закладні елементи, Фіксатори  
9. Витратні матеріали → …  
10. Піни, клеї, герметики → …  
11. Підшипники, сальники → …  
12. Композитна арматура… → …

Дублікати L2-імен (`Болти` тощо) — унікальність через `path` / `(parent, slug)`.

Команди: `seed_catalog` · `import_bolty_gvynty` · `reclassify_bolty_gvynty`  
Правила: `apps/catalog/classification.py`

## Поза MVP

- Нова Пошта API tables  
- Резерв `stock_qty` після оплати / refund UI  
- `/uk/` + `/ru/` i18n path  
- Порівняння товарів  
