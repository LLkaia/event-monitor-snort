from django.test import TestCase


class CustomTestCase(TestCase):
    def assertQuerySetAttributeContain(self, values, attributes, queryset):
        """Custom matcher of objects' attributes of QuerySet

        Check whether attributes of all objects in QuerySet
        contain given values.
        """
        list_of_values = [getattr(item, attribute) for attribute in attributes for item in queryset]
        for item in values:
            if item not in list_of_values:
                self.fail(f"Missing {values} in {list_of_values} of {attributes}.")
