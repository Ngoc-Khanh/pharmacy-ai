import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from beanie import PydanticObjectId
from models.medicine import Medicine
from services.medicine_recommendation_service import MedicineRecommendationService
from schemas.medicine_recommendation import MedicineInfo, MedicineRecommendation
from services.milvus_service import MilvusService

logger = logging.getLogger(__name__)


def serialize_medicine_data(medicine_data):
    """
    Custom serializer to handle datetime and other non-JSON serializable objects
    """
    def convert_value(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, PydanticObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_value(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_value(item) for item in obj]
        else:
            return obj
    
    return convert_value(medicine_data)


class DiagnosisMedicineService:
    def __init__(self):
        self.medicine_service = MedicineRecommendationService()

    async def debug_mongodb_connection(self) -> Dict[str, Any]:
        """
        Debug method để kiểm tra kết nối MongoDB và dữ liệu
        """
        try:
            # Khởi tạo database connection nếu cần
            from config.config import initiate_database
            await initiate_database()
            
            # Kiểm tra số lượng medicines trong database
            total_count = await Medicine.count()
            
            # Lấy một vài sample medicines
            sample_medicines = await Medicine.find().limit(3).to_list()
            
            # Lấy thông tin về các ID formats
            id_formats = []
            for medicine in sample_medicines:
                id_formats.append({
                    "_id": str(medicine.id) if medicine.id else "None",
                    "name": medicine.name,
                    "id_type": type(medicine.id).__name__
                })
            
            return {
                "total_medicines": total_count,
                "sample_id_formats": id_formats,
                "connection_status": "OK"
            }
            
        except Exception as e:
            logger.error(f"MongoDB debug failed: {e}")
            return {
                "total_medicines": 0,
                "sample_id_formats": [],
                "connection_status": f"ERROR: {str(e)}"
            }

    async def recommend_medicines_by_diagnosis(
        self,
        primary_diagnosis: str,
        symptoms: str,
        alternative_diagnoses: Optional[List[str]] = None,
        severity_level: str = "medium",
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Đề xuất thuốc dựa trên chẩn đoán và triệu chứng
        """
        try:
            # Tạo query tổng hợp từ chẩn đoán và triệu chứng
            search_queries = []
            
            # Query chính từ primary diagnosis
            search_queries.append({
                "query": primary_diagnosis,
                "weight": 0.5,
                "type": "diagnosis"
            })
            
            # Query từ symptoms
            search_queries.append({
                "query": symptoms,
                "weight": 0.3,
                "type": "symptoms"
            })
            
            # Query từ alternative diagnoses nếu có
            if alternative_diagnoses:
                for alt_diagnosis in alternative_diagnoses[:2]:  # Chỉ lấy 2 chẩn đoán thay thế đầu tiên
                    search_queries.append({
                        "query": alt_diagnosis,
                        "weight": 0.1,
                        "type": "alternative_diagnosis"
                    })
            
            # Thực hiện tìm kiếm cho từng query
            all_results = []
            
            for query_info in search_queries:
                # Tìm kiếm theo triệu chứng
                symptom_results = await self.medicine_service.search_medicines_by_symptoms(
                    symptoms=query_info["query"],
                    limit=limit * 2  # Lấy nhiều hơn để có thể filter và rank
                )
                
                # Thêm weight và type vào kết quả
                for result in symptom_results:
                    result["search_weight"] = query_info["weight"]
                    result["search_type"] = query_info["type"]
                    result["search_query"] = query_info["query"]
                
                all_results.extend(symptom_results)
            
            # Gộp và rank kết quả
            ranked_results = await self._rank_and_merge_results(
                all_results, 
                severity_level, 
                patient_age, 
                patient_gender,
                limit
            )
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"Error recommending medicines by diagnosis: {e}")
            raise

    async def _rank_and_merge_results(
        self,
        results: List[Dict[str, Any]],
        severity_level: str,
        patient_age: Optional[int],
        patient_gender: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Gộp và xếp hạng kết quả dựa trên nhiều yếu tố
        """
        try:
            # Group by medicine_id để tránh duplicate
            medicine_scores = {}
            
            for result in results:
                medicine_id = result.get("medicine_id")
                if not medicine_id:
                    continue
                
                base_score = result.get("similarity_score", 0.0)
                search_weight = result.get("search_weight", 1.0)
                search_type = result.get("search_type", "unknown")
                
                # Tính điểm tổng hợp
                weighted_score = base_score * search_weight
                
                if medicine_id in medicine_scores:
                    # Cộng dồn điểm nếu thuốc đã xuất hiện
                    medicine_scores[medicine_id]["total_score"] += weighted_score
                    medicine_scores[medicine_id]["search_types"].append(search_type)
                    medicine_scores[medicine_id]["search_count"] += 1
                else:
                    medicine_scores[medicine_id] = {
                        "result": result,
                        "total_score": weighted_score,
                        "search_types": [search_type],
                        "search_count": 1
                    }
            
            # Áp dụng bonus cho thuốc xuất hiện trong nhiều search
            for medicine_id, score_info in medicine_scores.items():
                if score_info["search_count"] > 1:
                    # Bonus 20% cho thuốc xuất hiện trong nhiều search
                    score_info["total_score"] *= 1.2
                
                # Bonus dựa trên severity level
                if severity_level == "high":
                    # Ưu tiên thuốc có rating cao và stock tốt
                    rating = score_info["result"].get("rating", 0)
                    if rating >= 4.0:
                        score_info["total_score"] *= 1.1
                
                # Cập nhật similarity_score và search_types trong result
                score_info["result"]["similarity_score"] = min(score_info["total_score"], 1.0)
                score_info["result"]["search_types"] = score_info["search_types"]
            
            # Sắp xếp theo điểm số
            sorted_results = sorted(
                [info["result"] for info in medicine_scores.values()],
                key=lambda x: x.get("similarity_score", 0),
                reverse=True
            )
            
            return sorted_results[:limit]
            
        except Exception as e:
            logger.error(f"Error ranking and merging results: {e}")
            return results[:limit]

    async def get_medicine_details_from_mongodb(
        self, medicine_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Lấy thông tin chi tiết thuốc từ MongoDB với multiple query strategies
        """
        try:
            medicines = {}
            
            # Strategy 1: Query by _id directly
            for medicine_id in medicine_ids:
                try:
                    medicine = await Medicine.get(medicine_id)
                    if medicine:
                        try:
                            medicine_dict = medicine.model_dump()
                        except AttributeError:
                            medicine_dict = medicine.dict()
                        # Serialize datetime and other objects
                        medicine_dict = serialize_medicine_data(medicine_dict)
                        medicines[medicine_id] = medicine_dict
                        continue
                except Exception as e:
                    logger.debug(f"Strategy 1 failed for {medicine_id}: {e}")
                
                # Strategy 2: Query by id field (not _id)
                try:
                    medicine = await Medicine.find_one(Medicine.id == medicine_id)
                    if medicine:
                        try:
                            medicine_dict = medicine.model_dump()
                        except AttributeError:
                            medicine_dict = medicine.dict()
                        # Serialize datetime and other objects
                        medicine_dict = serialize_medicine_data(medicine_dict)
                        medicines[medicine_id] = medicine_dict
                        continue
                except Exception as e:
                    logger.debug(f"Strategy 2 failed for {medicine_id}: {e}")
                
                # Strategy 3: Query using find with filter
                try:
                    medicine = await Medicine.find_one({"$or": [
                        {"_id": medicine_id},
                        {"id": medicine_id}
                    ]})
                    if medicine:
                        try:
                            medicine_dict = medicine.model_dump()
                        except AttributeError:
                            medicine_dict = medicine.dict()
                        # Serialize datetime and other objects
                        medicine_dict = serialize_medicine_data(medicine_dict)
                        medicines[medicine_id] = medicine_dict
                        continue
                except Exception as e:
                    logger.debug(f"Strategy 3 failed for {medicine_id}: {e}")
                
                # If all strategies fail, log warning
                logger.warning(f"Could not fetch medicine {medicine_id} with any strategy")
            
            logger.info(f"Successfully fetched {len(medicines)}/{len(medicine_ids)} medicines from MongoDB")
            return medicines
            
        except Exception as e:
            logger.error(f"Error getting medicine details from MongoDB: {e}")
            return {}

    def _generate_recommendation_reason(
        self,
        search_types: List[str],
        similarity_score: float,
        medicine_name: str
    ) -> str:
        """
        Tạo lý do đề xuất thuốc
        """
        reasons = []
        
        if "diagnosis" in search_types:
            reasons.append("phù hợp với chẩn đoán chính")
        
        if "symptoms" in search_types:
            reasons.append("có thể điều trị các triệu chứng")
        
        if "alternative_diagnosis" in search_types:
            reasons.append("phù hợp với chẩn đoán thay thế")
        
        if similarity_score >= 0.8:
            reasons.append("có độ tương đồng cao")
        elif similarity_score >= 0.6:
            reasons.append("có độ tương đồng tốt")
        
        if not reasons:
            reasons.append("được đề xuất dựa trên phân tích AI")
        
        return f"{medicine_name} " + " và ".join(reasons) + "."

    async def format_medicine_recommendations(
        self,
        vector_results: List[Dict[str, Any]],
        primary_diagnosis: str,
        symptoms: str
    ) -> List[MedicineRecommendation]:
        """
        Format kết quả thành MedicineRecommendation objects
        """
        try:
            # Lấy medicine_ids từ vector results
            medicine_ids = [result.get("medicine_id") for result in vector_results if result.get("medicine_id")]
            
            # Lấy thông tin chi tiết từ MongoDB
            mongodb_medicines = await self.get_medicine_details_from_mongodb(medicine_ids)
            
            recommendations = []
            
            for result in vector_results:
                medicine_id = result.get("medicine_id")
                if not medicine_id:
                    continue
                
                similarity_score = result.get("similarity_score", 0.0)
                
                # Nếu có thông tin từ MongoDB, sử dụng thông tin đầy đủ
                if medicine_id in mongodb_medicines:
                    mongodb_data = mongodb_medicines[medicine_id]
                    
                    # Tạo MedicineInfo object với thông tin đầy đủ từ MongoDB
                    medicine_info = MedicineInfo(
                        id=str(mongodb_data.get("id", medicine_id)),
                        name=mongodb_data.get("name", ""),
                        slug=mongodb_data.get("slug", ""),
                        description=mongodb_data.get("description", ""),
                        thumbnail=mongodb_data.get("thumbnail", {}),
                        price=mongodb_data.get("variants", {}).get("price", 0),
                        original_price=mongodb_data.get("variants", {}).get("original_price", 0),
                        discount_percent=mongodb_data.get("variants", {}).get("discount_percent", 0),
                        stock_status=mongodb_data.get("variants", {}).get("stock_status", ""),
                        rating=mongodb_data.get("ratings", {}).get("star", 0.0),
                        review_count=mongodb_data.get("ratings", {}).get("review_count", 0),
                        ingredients=mongodb_data.get("details", {}).get("ingredients", ""),
                        usage=mongodb_data.get("details", {}).get("usage", []),
                        dosage=mongodb_data.get("usageguide", {}).get("dosage", {}),
                        directions=mongodb_data.get("usageguide", {}).get("directions", []),
                        precautions=mongodb_data.get("usageguide", {}).get("precautions", []),
                        origin=mongodb_data.get("details", {}).get("paramaters", {}).get("origin", ""),
                        packaging=mongodb_data.get("details", {}).get("paramaters", {}).get("packaging", ""),
                        is_active=mongodb_data.get("variants", {}).get("is_active", False),
                        is_featured=mongodb_data.get("variants", {}).get("is_featured", False)
                    )
                else:
                    # Nếu không tìm thấy trong MongoDB, tạo thông tin cơ bản từ vector database
                    logger.warning(f"Medicine {medicine_id} not found in MongoDB, using basic info from vector DB")
                    medicine_info = MedicineInfo(
                        id=medicine_id,
                        name=result.get("name", f"Thuốc {medicine_id[:8]}..."),
                        slug=result.get("slug", ""),
                        description="Thông tin chi tiết không có sẵn",
                        thumbnail={"url": "", "alt": "No image", "public_id": ""},
                        price=result.get("price", 0),
                        original_price=result.get("price", 0),
                        discount_percent=0,
                        stock_status=result.get("stock_status", "UNKNOWN"),
                        rating=result.get("rating", 0.0),
                        review_count=0,
                        ingredients=result.get("active_ingredient", "Không có thông tin"),
                        usage=result.get("therapeutic_uses", "").split(",") if isinstance(result.get("therapeutic_uses"), str) and result.get("therapeutic_uses") else [],
                        dosage={"adult": "Theo chỉ định bác sĩ", "child": "Theo chỉ định bác sĩ"},
                        directions=["Sử dụng theo chỉ định của bác sĩ"],
                        precautions=["Tham khảo ý kiến bác sĩ trước khi sử dụng"],
                        origin="Không rõ",
                        packaging="Không rõ",
                        is_active=result.get("is_active", True),
                        is_featured=result.get("is_featured", False)
                    )

                
                # Tạo lý do đề xuất
                search_types = result.get("search_types", ["unknown"])
                recommendation_reason = self._generate_recommendation_reason(
                    search_types, similarity_score, medicine_info.name
                )
                
                # Tạo MedicineRecommendation object
                recommendation = MedicineRecommendation(
                    medicine=medicine_info,
                    similarity_score=similarity_score,
                    recommendation_reason=recommendation_reason
                )
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error formatting medicine recommendations: {e}")
            return [] 