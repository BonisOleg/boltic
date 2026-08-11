from django.test import SimpleTestCase

from apps.core.site_content_registry import CONTENT_SECTIONS, all_registry_block_keys


class SiteContentRegistryTests(SimpleTestCase):
    def test_block_keys_unique(self):
        keys = all_registry_block_keys()
        self.assertEqual(len(keys), len(set(keys)))

    def test_admin_model_names_unique(self):
        names = [s.admin_model_name for s in CONTENT_SECTIONS]
        self.assertEqual(len(names), len(set(names)))

    def test_visibility_keys_present(self):
        for section in CONTENT_SECTIONS:
            if not section.visibility_key:
                continue
            self.assertIn(
                (section.page_slug, section.visibility_key),
                section.blocks,
                msg=section.slug,
            )
