"""
Pydantic 모델 정의
API 요청/응답 스키마 및 데이터 검증을 위한 모델들
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ColumnRequest(BaseModel):
    """컬럼 생성 요청 스키마"""
    
    topic: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="컬럼 주제 (2-200자)",
        example="최근 대선 여론조사 결과에 대한 분석"
    )
    maxRevisionAttempts: Optional[int] = Field(
        default=3,
        ge=1,
        le=5,
        description="최대 수정 시도 횟수 (1-5회)",
        example=3
    )

    @validator("topic")
    def validate_topic(cls, v):
        """주제 검증"""
        if not v.strip():
            raise ValueError("주제는 공백일 수 없습니다.")
        
        # 금지된 키워드 검사 (보안상 민감한 내용 필터링)
        forbidden_keywords = ["욕설", "혐오", "비방", "개인정보"]
        topic_lower = v.lower()
        for keyword in forbidden_keywords:
            if keyword in topic_lower:
                raise ValueError(f"부적절한 내용이 포함되어 있습니다: {keyword}")
        
        return v.strip()


class Source(BaseModel):
    """참고 자료 스키마"""
    
    title: str = Field(..., description="자료 제목")
    uri: str = Field(..., description="자료 URL")


class MetaData(BaseModel):
    """메타데이터 스키마"""
    
    wordCount: int = Field(..., ge=0, description="단어 수")
    category: str = Field(..., description="카테고리")
    createdDate: str = Field(..., description="생성 일시 (ISO 8601)")
    sources: Optional[List[Source]] = Field(default=None, description="참고 자료 목록")


class ArticleData(BaseModel):
    """아티클 데이터 스키마"""
    
    title: str = Field(..., min_length=5, max_length=100, description="컬럼 제목")
    summary: str = Field(..., min_length=10, max_length=300, description="요약")
    content: str = Field(..., min_length=100, description="본문 내용")
    metadata: MetaData = Field(..., description="메타데이터")


class ColumnResponse(BaseModel):
    """컬럼 생성 응답 스키마"""
    
    success: bool = Field(..., description="성공 여부")
    article: ArticleData = Field(..., description="생성된 아티클")
    processedDate: str = Field(..., description="처리 완료 일시 (ISO 8601)")


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    
    success: bool = Field(default=False, description="성공 여부")
    error: str = Field(..., description="에러 메시지")
    processedDate: str = Field(..., description="처리 일시 (ISO 8601)")


# 서비스 레이어에서 사용하는 내부 모델들

class EvaluationResult(BaseModel):
    """컬럼 평가 결과 스키마"""
    
    scores: Dict[str, float] = Field(..., description="평가 점수")
    pass_: bool = Field(..., alias="pass", description="통과 여부")
    feedback: str = Field(..., description="피드백")
    revisedContent: str = Field(..., description="수정된 컨텐츠")


class GeneratedContent(BaseModel):
    """생성된 컨텐츠 스키마"""
    
    title: str = Field(..., description="제목")
    summary: str = Field(..., description="요약")
    content: str = Field(..., description="본문")
    sources: Optional[List[Source]] = Field(default=None, description="참고 자료")
    
    
class ParsedColumn(BaseModel):
    """파싱된 컬럼 스키마 (기존 TypeScript 타입 호환)"""
    
    title: str
    summary: str
    progressiveStance: List[str]
    conservativeStance: List[str]
    mainContentTitle: str
    mainContentBody: str
    conclusionTitle: str
    conclusionBody: str