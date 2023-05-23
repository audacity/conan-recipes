class BearerAuth:
    def __init__(self, key:str):
        self.key = key

    def __call__(self, r):
        r.headers["Authorization"] = f'Bearer {self.key}'
        return r
