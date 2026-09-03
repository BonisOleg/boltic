# БОЛТіК° — business-logic.md (MVP)

Джерела: `boltiksitemap.pdf`, `tables.md`, рішення 2026-07-22.

## Архітектура

```
HTTP/HTMX → View → Service → QuerySet/Model → Template / partial / redirect
```

- Бізнес-правила лише в **services** (не в шаблонах).
- Публічні QuerySet завжди з `is_active=True` / `is_published=True`.
- Одиниця купівлі — **тільки `ProductSKU`**.

---

## Фінальні рішення (закриті питання)

| # | Питання | Рішення |
|---|---------|---------|
| 1 | Кількість vs `min_party` | `qty >= min_party`, крок = **1**. Опт від окремого `wholesale_from_qty`. |
| 2 | Наявність на PDP | Усі **active** SKU видимі. `in_stock` — звичайна кнопка; `on_order` — бейдж «Під замовлення», кнопка **активна** (передзамовлення). Немає окремого «немає» в MVP — якщо треба зняти з продажу → `is_active=False`. |
| 3 | Оплата | Замовлення створюється з `payment_status=pending`. **LiqPay** — модуль є, підключення до checkout пізніше. |
| 4 | Документація | Цей файл + `tables.md`. |

---

## Інваріанти

1. У кошик / wishlist / OrderItem потрапляє лише `ProductSKU`.
2. Canonical URL категорії = `/katalog/{path}/` **без** facet-query.
3. Ціна в `OrderItem` — **знімок** на момент `place()` (не жива з SKU).
4. Гість може оформити й оплатити; wishlist і відгук — лише auth.
5. Неактивні Group/SKU не в публічних видачах.
6. Успіх замовлення для гостя — лише з `access_token` (не голий `number`).

---

## 1. Каталог — читання і фільтрація

### `CategoryCatalogService`

**`resolve_path(path) → Category`**
- `Category.objects.get(path=normalized, is_active=True)` або 404.
- Нормалізація: trim, trailing `/`.

**L1 (`level=1`)**
- Показати L2-дітей (`children`, active, `sort_order`).
- Лістинг груп: усі `ProductGroup` у дереві L1 (`category__parent=l1`) **або** лише навігація без сітки — MVP: сітка всіх груп L1 з пагінацією.

**L2 (`level=2`)**
- База: `ProductGroup.objects.filter(category=cat, is_active=True)`.

### Facets (`?material=a2&diametr=m8`)

**`FacetService.parse(request.GET) → dict[str, list[str]]`**
- Whitelist лише відомих `FacetAttribute.code`.
- Кілька значень одного коду: `?diametr=m6&diametr=m8` → OR всередині атрибута.
- Різні коди → **AND**.

**`FacetService.apply(groups_qs, selected) → qs`**
- Група проходить, якщо має ≥1 `ProductSKU` з `is_active=True`, що задовольняє всі вибрані атрибути (через `SKUFacet` / `FacetValue.slug`).
- `distinct()`.

**Facet counts (для UI)**
- Для кожного атрибута рахувати values на QS, відфільтрованому **всіма іншими** атрибутами (classic faceted nav).

**Сортування:** `?sort=name|price|new`
- `price` → `annotate(price_from=Min("skus__price", filter=Q(skus__is_active=True)))`.

**Пагінація:** 24 групи / сторінка.

**HTMX:** partial сітки товарів + facet counts; `pushState` з query; **rel=canonical** без facets.

**Картка в лістингу:** назва, primary image, `price_from`, бейджі `is_top` / `is_promo`.

---

## 2. PDP — `/tovar/{slug}/`

### `ProductService.get_pdp(slug)`

1. `ProductGroup` active + 404.
2. Prefetch: `images`, `documents`, `skus` (active), published `reviews`.
3. Default tab = **Асортимент**.
4. На групі **немає** кнопки «Купити».

### Відображення SKU (рішення #2)

| `stock_status` | UI | Купівля |
|----------------|----|---------|
| `in_stock` | бейдж «В наявності» | так |
| `on_order` | бейдж «Під замовлення» | так |
| `is_active=False` | не показувати | — |

Якщо задано `stock_qty` — обмежує qty у кошику; при `place_order` залишок **списується** атомарно (`select_for_update` + `F()`).

### `CartService.add` з рядка (рішення #1)

```
valid_qty(sku, qty):
  qty >= sku.min_party   # крок = 1
```

- UI: `−` / `+` кроком **1**; input blur → clamp ≥ min і ≤ stock.
- Якщо рядок у кошику є: `new_qty = old + qty`, знову нормалізація.

### Ціна рядка

```
unit_price_for_qty(sku, qty):
  if party_price and wholesale_from_qty and qty >= wholesale_from_qty:
      return party_price          # грн/шт, без sale
  return sale_price or price      # роздріб
line = unit_price * qty
```

`pack_qty` — лише display на картці.

---

## 3. Пошук — `/katalog/search/`

### `SearchService.suggest(q)` (q ≥ 2)
- До 8 `ProductGroup` по `name`/`slug`.
- До 4 `ProductSKU` по `article`/`name`.
- Лише active.

### `SearchService.search(q)`
- Ті самі критерії, пагінація груп.
- Клік по артикулу → `/tovar/{group.slug}/?sku={article}` (підсвіт рядка).

---

## 4. Кошик і wishlist

### `CartService.resolve(request)`
- Auth → cart by `user` (get_or_create).
- Anon → `session_key` (форсувати session).
- **Login merge:** session items → user cart (`qty` сумувати, потім `normalize_qty` / clamp); session cart видалити.

### Sync при відкритті кошика
- Неактивний SKU → прибрати + flash.
- Якщо `qty` стала невалідною відносно нового `min_party` / stock → підняти або clamp.

### Totals
- `line = qty * unit_price_for_qty(sku, qty)` (жива ціна).
- `subtotal = sum(lines)`.

### Wishlist
- Лише auth; item = SKU; unique(user, sku).

---

## 5. Checkout + онлайн-оплата (LiqPay)

### Потік

```
/oformlennya/ (форма)
    → OrderService.place()          # Order + Items, payment_status=pending
    → PaymentService.create_checkout(order)  # PaymentTransaction
    → redirect LiqPay (або embed)
    → LiqPay callback/webhook
    → PaymentService.handle_webhook()
    → order.payment_status=paid, status=paid
    → /oformlennya/uspikh/{number}/?token=…
```

URL (карта + доповнення):
- `/oformlennya/` — форма
- `/payments/liqpay/callback/` — server-to-server (CSRF exempt, signature check)
- `/payments/liqpay/result/` — return URL браузера
- `/oformlennya/uspikh/{number}/` — успіх (перевірка `token`)

### `OrderService.place(cart, form, user|None)`

1. Валідація рядків: active, `valid_qty`, `price > 0`.
2. Форма: `customer_name`, `phone` обовʼязково; `email` бажано для чека LiqPay.
3. `user = request.user if authenticated else None`.
4. `number = BLT-YYYYMMDD-XXXX` (унікальний).
5. `access_token = uuid4` — доступ гостя до success/деталей.
6. Snapshot кожного SKU → `OrderItem` (+ vat поля).
7. `total = sum(line_total)`; `payment_status=pending`; `status=new`.
8. Очистити cart items **після** успішного create (замовлення вже є навіть якщо оплата зірветься).
9. Повернути `order` → далі PaymentService.

### `PaymentService` (app `payments`)

**Провайдер MVP:** LiqPay (UA, карта / Apple Pay тощо через їх віджет).

**`PaymentTransaction`**
- FK `order`
- `provider = liqpay`
- `status`: created | redirected | success | failure | refunded
- `amount`, `currency=UAH`
- `external_id` / `liqpay_order_id`
- `raw_request` / `raw_response` (JSON) — для аудиту
- timestamps

**`create_checkout(order)`**
- Створити transaction `created`.
- Підписати LiqPay data (private key).
- status → `redirected`.

**`handle_webhook(payload, signature)`**
- Verify signature.
- Ідемпотентність: повторний success не дублює side-effects.
- success → `order.payment_status=paid`, `order.status=paid`, tx=`success`.
- failure → `payment_status=failed`, tx=`failure`; замовлення лишається `new` (можна «оплатити знову»).

**Повторна оплата:** якщо `pending`/`failed` — нова `PaymentTransaction`, старі не success не чіпати як фінал.

### Успіх / безпека гостя
- View success: `Order.objects.get(number=…, access_token=token)` або auth owner.
- Без валідного token → 404.

---

## 6. Ціни і ПДВ

| Контекст | Правило |
|----------|---------|
| Вітрина / кошик | `unit_price_for_qty(sku, qty)` |
| Підпис | якщо `price_includes_vat`: «в т.ч. ПДВ {vat_rate}%» |
| Net (звіти) | `price / (1 + vat_rate/100)` |
| Checkout | знімок `unit_price` / `line_total` у `OrderItem` |
| Опт | `party_price` грн/шт при `qty ≥ wholesale_from_qty` |
| Акція | `sale_price` лише в роздробі (нижче порога опту) |
| LiqPay amount | = `order.total` (UAH), коли підключать checkout |

---

## 7. Відгуки · бренди · контент

| Домен | Read | Write |
|-------|------|-------|
| Review | `is_published` на PDP | login; `is_published=False` до модерації |
| Brand | active + groups | admin |
| Collection / Promotion | published (+ вікно дат) | admin |
| StaticPage / ContactBranch | slug / active | admin |
| Home | HomeBlock + `is_top` + promos | admin |

---

## 8. Карта services (код)

| Service | Методи | App |
|---------|--------|-----|
| `CategoryCatalogService` | `resolve_path`, `list_groups`, `facet_state` | catalog |
| `ProductService` | `get_pdp`, `assortment_qs` | catalog |
| `SearchService` | `suggest`, `search` | catalog |
| `CartService` | `resolve`, `add`, `update`, `remove`, `merge_on_login`, `normalize_qty`, `totals` | cart |
| `OrderService` | `place`, `get_for_success` | orders |
| `PaymentService` | `create_checkout`, `handle_webhook`, `retry` | payments |
| `ReviewService` | `create_pending` | reviews |
| `Pricing` | `line_total`, `display_price`, `net_from_gross` | catalog |

### Правила qty (спільні)

```python
def normalize_qty(qty: int, min_party: int) -> int:
    if min_party < 1:
        min_party = 1
    if qty < min_party:
        return min_party
    return int(qty)
```

`add`/`update`: auto-normalize до `≥ min_party` і clamp по `stock_qty`.

---

## 9. Sitemap-coverage verify (boltiksitemap.pdf)

| URL | urls | view | template | Статус |
|-----|------|------|----------|--------|
| `/` | ✅ | content.HomeView | ✅ | ✅ |
| `/robots.txt` | ✅ | core.RobotsTxtView | — | ✅ |
| `/sitemap.xml` | ✅ | django sitemaps | — | ✅ |
| `/katalog/` | ✅ | catalog.CatalogRootView | ✅ | ✅ |
| `/katalog/{path}/` | ✅ | catalog.CategoryView | ✅ | ✅ |
| `/katalog/search/` | ✅ | catalog.search | ✅ | ✅ |
| `/tovar/{slug}/` | ✅ | catalog.ProductDetailView | ✅ | ✅ |
| `/tovar/{slug}/vidguk/` | ✅ | catalog.product_review | — | ✅ |
| `/pidbirka/{slug}/` | ✅ | catalog.CollectionDetailView | ✅ | ✅ |
| `/brendy/` · `/brendy/{slug}/` | ✅ | Brand* | ✅ | ✅ |
| `/aktsiyi/` · `/{slug}/` | ✅ | content.Promo* | ✅ | ✅ |
| `/novyny/` · `/{slug}/` | ✅ | content.News* | ✅ | ✅ |
| `/kontakty/` | ✅ | content.ContactsView | ✅ | ✅ |
| `/oplata-i-dostavka/` тощо | ✅ | StaticPageView | ✅ | ✅ |
| `/koshyk/` + add/update/remove | ✅ | cart.* | ✅ | ✅ |
| `/oformlennya/` · success | ✅ | orders.* | ✅ | ✅ |
| `/payments/liqpay/*` | ✅ | payments.* | ✅ | ✅ (додано до карти) |
| `/bazhane/` | ✅ | cart.wishlist | ✅ | ✅ |
| `/login/` `/register/` `/logout/` | ✅ | accounts.* | ✅ | ✅ |
| `/kabinet/` · orders · profile | ✅ | accounts.* | ✅ | ✅ |
| 404/500 templates | — | — | поза MVP UI | поза MVP |

## 10. Що поза цією логікою (наступні етапи)

- Підключення LiqPay до checkout (модуль уже є)
- Нова Пошта API
- Refund flow UI
- i18n `/uk/` `/ru/`
- Полірований UI (зараз stub-шаблони)
