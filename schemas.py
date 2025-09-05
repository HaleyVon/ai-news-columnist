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
        example="나경원 추미애"
    )
    maxRevisionAttempts: Optional[int] = Field(
        default=3,
        ge=1,
        le=5,
        description="최대 수정 시도 횟수 (1-5회)",
        example=3
    )
    daysBack: Optional[int] = Field(
        default=7,
        ge=1,
        le=30,
        description="뉴스 검색 기간 (1-30일, 기본값 7일)",
        example=7
    )
    searchMode: Optional[str] = Field(
        default="title",
        description="검색 범위 ('title': 제목만, 'all': 제목+내용, 기본값 'title')",
        example="title"
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

    @validator("searchMode")
    def validate_search_mode(cls, v):
        """검색 모드 검증"""
        if v not in ["title", "all"]:
            raise ValueError("searchMode는 'title' 또는 'all'만 허용됩니다.")
        return v


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


class NewsSearchResult(BaseModel):
    """뉴스 검색 결과 스키마"""
    
    title: str = Field(..., description="뉴스 제목")
    description: str = Field(..., description="뉴스 요약")
    pubDate: str = Field(..., description="발행일")
    originalLink: Optional[str] = Field(default=None, description="원본 링크")


class NewsPreviewResponse(BaseModel):
    """뉴스 미리보기 응답 스키마"""
    
    success: bool = Field(..., description="성공 여부")
    topic: str = Field(..., description="검색 주제")
    searchPeriod: int = Field(..., description="검색 기간 (일)")
    newsCount: int = Field(..., description="검색된 뉴스 수")
    newsItems: List[NewsSearchResult] = Field(..., description="검색된 뉴스 목록 (최대 5개 미리보기)")
    totalAvailable: int = Field(..., description="전체 사용 가능한 뉴스 수")
    searchQuality: str = Field(..., description="검색 품질 평가 (excellent/good/fair/poor)")
    recommendation: str = Field(..., description="사용자에게 보여줄 권장사항")
    processedDate: str = Field(..., description="처리 일시 (ISO 8601)")


class ColumnGenerationConfirmRequest(BaseModel):
    """컬럼 생성 확인 요청 스키마"""
    
    topic: str = Field(..., description="컬럼 주제")
    daysBack: int = Field(default=7, description="뉴스 검색 기간")
    maxRevisionAttempts: Optional[int] = Field(default=3, description="최대 수정 시도 횟수")
    searchMode: Optional[str] = Field(default="title", description="검색 범위")
    proceed: bool = Field(..., description="컬럼 생성 진행 여부")


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