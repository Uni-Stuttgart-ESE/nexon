class ErrorWithStatusCode(Exception):
  """Base class for exceptions with a status code."""
  def __init__(self, status_code, message):
      self.message = message
      self.status_code = status_code
      super().__init__(self.message)
      
  def as_http_exception(self):
      """Convert to FastAPI HTTPException."""
      from fastapi import HTTPException
      return HTTPException(status_code=self.status_code, detail=self.message)

class BadRequestError(ErrorWithStatusCode):
  """Exception raised for bad requests."""
  def __init__(self, message="Bad request"):
      super().__init__(400, message)

class NotFoundError(ErrorWithStatusCode):
  """Exception raised when a resource is not found."""
  def __init__(self, message="Resource not found"):
      super().__init__(404, message)
        
class InternalServerError(ErrorWithStatusCode):
  """Exception raised for internal server errors."""
  def __init__(self, message="Internal server error"):
      super().__init__(500, message)