class FakeStorageService:
    def build_image_url(self, key: str) -> str:
        return f"https://fake-storage.test/{key}"

    def upload(self, key: str, contents: bytes, ext: str) -> None:
        pass

    def upload_many(self, files: list[tuple[str, bytes, str]]) -> None:
        pass

    def delete_many(self, keys: list[str]) -> None:
        pass
