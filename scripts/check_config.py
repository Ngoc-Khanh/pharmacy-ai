#!/usr/bin/env python3
"""
Script kiểm tra cấu hình và kết nối trước khi chạy sync
Sử dụng: python scripts/check_config.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import cohere
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pymilvus import connections, utility

from config.config import Settings
from models.medicine import Medicine


class ConfigChecker:
    def __init__(self):
        self.settings = Settings()
        self.errors = []
        self.warnings = []
    def check_environment_variables(self):
        """Kiểm tra các biến môi trường cần thiết"""
        print("🔍 Kiểm tra biến môi trường...")
        required_vars = {
            "DATABASE_URL": self.settings.DATABASE_URL,
            "DATABASE_NAME": self.settings.DATABASE_NAME,
            "COHERE_API_KEY": self.settings.COHERE_API_KEY,
            "MILVUS_URI": self.settings.MILVUS_URI,
            "MILVUS_TOKEN": self.settings.MILVUS_TOKEN,
        }
        for var_name, var_value in required_vars.items():
            if not var_value:
                self.errors.append(f"❌ {var_name} không được cấu hình")
            else:
                print(
                    f"✅ {var_name}: {'*' * (len(str(var_value)) - 4) + str(var_value)[-4:]}"
                )
        # Optional vars
        optional_vars = {
            "COHERE_EMBEDDING_MODEL": self.settings.COHERE_EMBEDDING_MODEL,
            "MILVUS_COLLECTION_NAME": self.settings.MILVUS_COLLECTION_NAME,
            "EMBEDDING_DIMENSION": self.settings.EMBEDDING_DIMENSION,
        }
        for var_name, var_value in optional_vars.items():
            if var_value:
                print(f"✅ {var_name}: {var_value}")
            else:
                self.warnings.append(f"⚠️  {var_name} sử dụng giá trị mặc định")

    async def check_mongodb_connection(self):
        """Kiểm tra kết nối MongoDB"""
        print("\n🔍 Kiểm tra kết nối MongoDB...")
        try:
            client = AsyncIOMotorClient(self.settings.DATABASE_URL)
            database = client[self.settings.DATABASE_NAME]
            # Test connection
            await client.admin.command("ping")
            print("✅ Kết nối MongoDB thành công")
            # Initialize beanie
            await init_beanie(database=database, document_models=[Medicine])
            print("✅ Khởi tạo Beanie thành công")
            # Check medicines collection
            medicine_count = await Medicine.count()
            print(f"✅ Tìm thấy {medicine_count} medicines trong database")
            if medicine_count == 0:
                self.warnings.append("⚠️  Không có dữ liệu medicine trong database")
            # Test sample medicine
            if medicine_count > 0:
                sample_medicine = await Medicine.find_one()
                if sample_medicine:
                    print(f"✅ Sample medicine: {sample_medicine.name}")
                    # Check required fields
                    required_fields = [
                        "name",
                        "description",
                        "details",
                        "usageguide",
                        "variants",
                    ]
                    missing_fields = []
                    for field in required_fields:
                        if not hasattr(sample_medicine, field) or not getattr(
                            sample_medicine, field
                        ):
                            missing_fields.append(field)
                    if missing_fields:
                        self.warnings.append(
                            f"⚠️  Sample medicine thiếu fields: {', '.join(missing_fields)}"
                        )
                    else:
                        print("✅ Cấu trúc dữ liệu medicine hợp lệ")
        except Exception as e:
            self.errors.append(f"❌ Lỗi kết nối MongoDB: {e}")

    def check_cohere_connection(self):
        """Kiểm tra kết nối Cohere API"""
        print("\n🔍 Kiểm tra kết nối Cohere API...")
        try:
            client = cohere.ClientV2(self.settings.COHERE_API_KEY)
            # Test embedding
            test_text = "Thuốc giảm đau paracetamol"
            response = client.embed(
                texts=[test_text],
                model=self.settings.COHERE_EMBEDDING_MODEL,
                input_type="search_document",
                embedding_types=["float"],
            )
            embedding = response.embeddings.float[0]
            print(f"✅ Kết nối Cohere API thành công")
            print(f"✅ Model: {self.settings.COHERE_EMBEDDING_MODEL}")
            print(f"✅ Embedding dimension: {len(embedding)}")
            if len(embedding) != self.settings.EMBEDDING_DIMENSION:
                self.warnings.append(
                    f"⚠️  Embedding dimension không khớp: "
                    f"expected {self.settings.EMBEDDING_DIMENSION}, got {len(embedding)}"
                )
        except Exception as e:
            self.errors.append(f"❌ Lỗi kết nối Cohere API: {e}")

    def check_milvus_connection(self):
        """Kiểm tra kết nối Milvus"""
        print("\n🔍 Kiểm tra kết nối Milvus...")
        try:
            connections.connect(
                alias="default",
                uri=self.settings.MILVUS_URI,
                token=self.settings.MILVUS_TOKEN,
            )
            print("✅ Kết nối Milvus thành công")
            # Check if collection exists
            collection_name = self.settings.MILVUS_COLLECTION_NAME
            if utility.has_collection(collection_name):
                print(f"✅ Collection '{collection_name}' đã tồn tại")
                # Get collection info
                from pymilvus import Collection
                collection = Collection(collection_name)
                num_entities = collection.num_entities
                print(f"✅ Số lượng entities hiện tại: {num_entities}")
                if num_entities > 0:
                    self.warnings.append(
                        f"⚠️  Collection đã có {num_entities} entities. "
                        f"Sử dụng --recreate-collection để tạo lại."
                    )
            else:
                print(
                    f"ℹ️  Collection '{collection_name}' chưa tồn tại (sẽ được tạo khi sync)"
                )
        except Exception as e:
            self.errors.append(f"❌ Lỗi kết nối Milvus: {e}")

    def print_summary(self):
        """In tổng kết kiểm tra"""
        print("\n" + "=" * 50)
        print("📋 TỔNG KẾT KIỂM TRA")
        print("=" * 50)
        if not self.errors and not self.warnings:
            print("🎉 Tất cả cấu hình đều OK! Sẵn sàng để sync.")
            return True
        if self.errors:
            print("\n❌ CÁC LỖI CẦN SỬA:")
            for error in self.errors:
                print(f"  {error}")
        if self.warnings:
            print("\n⚠️  CÁC CẢNH BÁO:")
            for warning in self.warnings:
                print(f"  {warning}")
        if self.errors:
            print("\n❌ Vui lòng sửa các lỗi trước khi chạy sync!")
            return False
        else:
            print("\n✅ Có thể chạy sync (có một số cảnh báo)")
            return True

    async def run_all_checks(self):
        """Chạy tất cả các kiểm tra"""
        print("🚀 BẮT ĐẦU KIỂM TRA CẤU HÌNH")
        print("=" * 50)
        # Check environment variables
        self.check_environment_variables()
        # Check connections
        await self.check_mongodb_connection()
        self.check_cohere_connection()
        self.check_milvus_connection()
        # Print summary
        return self.print_summary()


async def main():
    """Main function"""
    try:
        checker = ConfigChecker()
        success = await checker.run_all_checks()
        if success:
            print("\n🚀 Để chạy sync, sử dụng:")
            print("   python scripts/run_sync.py")
            print("   python scripts/sync_medicines_to_milvus.py")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
