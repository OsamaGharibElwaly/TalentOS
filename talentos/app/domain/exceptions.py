class TalentOSError(Exception):
    """Base class for domain errors."""


class ForbiddenError(TalentOSError):
    """The user lacks the permission for an action."""


class TenantMismatchError(TalentOSError):
    """The user and the target resource belong to different tenants."""


class NotFoundError(TalentOSError):
    """The requested resource does not exist within the tenant."""


class RubricValidationError(TalentOSError):
    """A job rubric is structurally invalid."""


class ProfileValidationError(TalentOSError):
    """A parsed candidate profile violates the bounded schema."""


class QueueLimitError(TalentOSError):
    """An ingestion batch exceeds the local queue capacity."""


class InferenceConfigError(TalentOSError):
    """A non-local inference backend was requested without an adapter."""


class InvalidStageTransitionError(TalentOSError):
    """The requested application stage transition is not allowed."""
