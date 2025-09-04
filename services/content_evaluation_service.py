"""
컨텐츠 평가 서비스
생성된 정치 컬럼의 품질을 평가하고 수정하는 전용 모듈
"""

import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI

from schemas import EvaluationResult
from core.exceptions import GeminiAPIException, ContentGenerationException
from .prompts import PromptGenerator

logger = logging.getLogger(__name__)


class ContentEvaluationService:
    """컨텐츠 평가 전용 서비스 클래스"""
    
    def __init__(self, api_key: str):
        """
        컨텐츠 평가 서비스 초기화
        
        Args:
            api_key: OpenAI API 키
        """
        self.api_key = api_key
        
        # OpenAI 클라이언트 초기화
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # 평가용 모델 설정 (일관성을 위해 낮은 temperature)
        self.model = "gpt-4.1-mini"
        
        self.prompt_generator = PromptGenerator()
    
    async def evaluate_and_revise(self, content: str) -> EvaluationResult:
        """
        컨텐츠를 평가하고 필요시 수정
        
        Args:
            content: 평가할 컨텐츠
            
        Returns:
            EvaluationResult: 평가 결과 및 수정된 컨텐츠
        """
        try:
            logger.info("컨텐츠 품질 평가 시작")
            
            # 평가 프롬프트 생성
            prompt = self.prompt_generator.get_revision_prompt(content)
            
            # OpenAI API 호출하여 평가 수행 (JSON 모드)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 콘텐츠 품질 관리 전문가입니다. 주어진 컬럼을 평가하고 JSON 형식으로 결과를 반환해주세요."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # 평가 일관성을 위해 낮은 temperature
                max_completion_tokens=4000
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise ContentGenerationException("평가 API가 빈 응답을 반환했습니다.")
            
            # JSON 응답 파싱
            evaluation_data = json.loads(response.choices[0].message.content)
            
            # EvaluationResult 객체 생성
            result = self._parse_evaluation_result(evaluation_data)
            
            logger.info(f"컨텐츠 평가 완료: 통과여부={result.pass_}")
            logger.debug(f"평가 점수: {result.scores}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"평가 결과 JSON 파싱 실패: {str(e)}")
            raise ContentGenerationException(f"평가 결과 파싱 오류: {str(e)}")
        except Exception as e:
            logger.error(f"컨텐츠 평가 중 오류: {str(e)}")
            raise ContentGenerationException(f"평가 중 오류가 발생했습니다: {str(e)}")
    
    def _parse_evaluation_result(self, evaluation_data: Dict[str, Any]) -> EvaluationResult:
        """
        평가 API 응답 데이터를 EvaluationResult 객체로 변환
        
        Args:
            evaluation_data: 평가 API 응답 데이터
            
        Returns:
            EvaluationResult: 파싱된 평가 결과
        """
        try:
            # 점수 정보 추출
            scores_data = evaluation_data.get("scores", {})
            scores = {
                "format": scores_data.get("format", 0),
                "balance": scores_data.get("balance", 0), 
                "readability": scores_data.get("readability", 0),
                "completeness": scores_data.get("completeness", 0),
                "objectivity": scores_data.get("objectivity", 0)
            }
            
            # 통과 여부 확인
            pass_status = evaluation_data.get("pass", False)
            
            # 피드백 메시지
            feedback = evaluation_data.get("feedback", "평가 완료")
            
            # 수정된 컨텐츠
            revised_content = evaluation_data.get("revisedContent", "")
            
            # EvaluationResult 객체 생성 (alias 사용하여 딕셔너리로)
            result_data = {
                "scores": scores,
                "pass": pass_status,  # alias 사용
                "feedback": feedback,
                "revisedContent": revised_content
            }
            result = EvaluationResult.model_validate(result_data)
            
            # 평가 결과 로깅
            total_score = sum(scores.values()) / len(scores) if scores else 0
            logger.info(f"평가 결과 - 평균점수: {total_score:.1f}, 통과: {pass_status}")
            
            if not pass_status:
                logger.warning(f"품질 기준 미달 - 피드백: {feedback[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"평가 결과 파싱 중 오류: {str(e)}")
            raise ContentGenerationException(f"평가 결과 처리 실패: {str(e)}")
    
    async def get_quality_score(self, content: str) -> Dict[str, float]:
        """
        컨텐츠의 품질 점수만 간단히 계산
        
        Args:
            content: 평가할 컨텐츠
            
        Returns:
            Dict[str, float]: 각 항목별 점수
        """
        try:
            logger.info("간단 품질 점수 계산 시작")
            
            evaluation = await self.evaluate_and_revise(content)
            
            logger.info(f"품질 점수 계산 완료: 평균 {sum(evaluation.scores.values()) / len(evaluation.scores):.1f}")
            return evaluation.scores
            
        except Exception as e:
            logger.error(f"품질 점수 계산 실패: {str(e)}")
            # Fallback: 기본 점수 반환
            return {
                "format": 70.0,
                "balance": 70.0,
                "readability": 70.0,
                "completeness": 70.0,
                "objectivity": 70.0
            }
    
    def calculate_overall_quality(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """
        전체적인 품질 지표 계산
        
        Args:
            scores: 각 항목별 점수
            
        Returns:
            Dict[str, Any]: 전체 품질 지표
        """
        try:
            # 평균 점수 계산
            average_score = sum(scores.values()) / len(scores) if scores else 0
            
            # 최저 점수 찾기
            min_score = min(scores.values()) if scores else 0
            min_category = min(scores.keys(), key=lambda k: scores[k]) if scores else "N/A"
            
            # 품질 등급 결정
            if average_score >= 90:
                grade = "우수"
            elif average_score >= 80:
                grade = "양호"
            elif average_score >= 70:
                grade = "보통"
            else:
                grade = "개선필요"
            
            # 통과 여부 (모든 항목이 85점 이상)
            passing = all(score >= 85 for score in scores.values()) if scores else False
            
            quality_info = {
                "averageScore": round(average_score, 1),
                "grade": grade,
                "passing": passing,
                "weakestCategory": min_category,
                "weakestScore": round(min_score, 1),
                "detailedScores": scores
            }
            
            logger.debug(f"품질 지표 계산 완료: {grade} ({average_score:.1f}점)")
            
            return quality_info
            
        except Exception as e:
            logger.error(f"품질 지표 계산 실패: {str(e)}")
            return {
                "averageScore": 0.0,
                "grade": "오류",
                "passing": False,
                "weakestCategory": "N/A",
                "weakestScore": 0.0,
                "detailedScores": {}
            }
    
    def is_content_acceptable(self, scores: Dict[str, float], threshold: float = 85.0) -> bool:
        """
        컨텐츠가 허용 가능한 품질인지 확인
        
        Args:
            scores: 각 항목별 점수
            threshold: 허용 기준 점수 (기본 85점)
            
        Returns:
            bool: 허용 가능 여부
        """
        if not scores:
            return False
        
        # 모든 항목이 기준점 이상인지 확인
        acceptable = all(score >= threshold for score in scores.values())
        
        logger.info(f"컨텐츠 허용성 검사: {'통과' if acceptable else '미통과'} (기준: {threshold}점)")
        
        return acceptable