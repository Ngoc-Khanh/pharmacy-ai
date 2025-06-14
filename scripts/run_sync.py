#!/usr/bin/env python3
"""
Script đơn giản để chạy đồng bộ dữ liệu Medicine từ MongoDB lên Milvus
Sử dụng: python scripts/run_sync.py [options]
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.sync_medicines_to_milvus import MedicineDataSyncer


async def main():
    parser = argparse.ArgumentParser(
        description="Đồng bộ dữ liệu Medicine từ MongoDB lên Milvus"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Chỉ kiểm tra kết quả đồng bộ, không thực hiện sync",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Số lượng medicine xử lý trong mỗi batch (mặc định: 10)",
    )
    parser.add_argument(
        "--recreate-collection",
        action="store_true",
        help="Tạo lại collection Milvus (xóa dữ liệu cũ)",
    )

    args = parser.parse_args()

    try:
        syncer = MedicineDataSyncer()
        syncer.batch_size = args.batch_size
        if args.verify_only:
            print("🔍 Đang kiểm tra kết quả đồng bộ...")
            await syncer.verify_sync()
        else:
            if args.recreate_collection:
                print("🔄 Sẽ tạo lại collection Milvus...")
            print(f"🚀 Bắt đầu đồng bộ dữ liệu (batch size: {args.batch_size})...")
            await syncer.sync_all_medicines()
            print("✅ Đồng bộ hoàn thành! Đang kiểm tra kết quả...")
            await syncer.verify_sync()
        print("🎉 Hoàn thành!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
