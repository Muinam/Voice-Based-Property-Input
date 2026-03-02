# class PropertyState:
#     def __init__(self):
#         self.data = {
#             "title": "",
#             "description": "",
#             "property_type": None,
#             "city": None,          # New: only city
#             "area": None,          # New: area/address
#             "size": None,
#             "bedrooms": None,
#             "bathrooms": None,
#             "price": None,
#             "listing_type": None,
#             "features": []
#         }

#     def update_from_dict(self, d):
#         for k, v in d.items():
#             if v is not None:
#                 self.data[k] = v

#     def is_complete(self):
#         required = ["property_type", "city", "area", "size", "bedrooms", "bathrooms", "price", "listing_type"]
#         return all(self.data.get(k) is not None for k in required)

#     def get_missing(self):
#         required = ["property_type", "city", "area", "size", "bedrooms", "bathrooms", "price", "listing_type"]
#         return [k for k in required if self.data.get(k) is None]

class PropertyState:
    def __init__(self):
        self.data = {}

    def update_from_dict(self, d):
        for k, v in d.items():
            if v is not None:
                self.data[k] = v