from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    VIEWER = "viewer"


class Permission(str, Enum):
    JOB_CREATE = "job:create"
    JOB_READ = "job:read"
    APPLICATION_CREATE = "application:create"
    APPLICATION_READ = "application:read"
    TELEMETRY_READ = "telemetry:read"


class IngestionStatus(str, Enum):
    QUEUED = "QUEUED"
    PARSING = "PARSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class ApplicationStage(str, Enum):
    NEW = "NEW"
    SCREENED = "SCREENED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    FINAL_REVIEW = "FINAL_REVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"


class HireRecommendation(str, Enum):
    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NO_HIRE = "NO_HIRE"
