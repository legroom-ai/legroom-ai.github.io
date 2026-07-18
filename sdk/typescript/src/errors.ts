/**
 * Error hierarchy matching Python legroom.exceptions.
 */

export class LegroomError extends Error {
  details?: Record<string, any>;

  constructor(message: string, details?: Record<string, any>) {
    super(message);
    this.name = "LegroomError";
    this.details = details;
  }
}

export class LegroomConnectionError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "LegroomConnectionError";
  }
}

export class LegroomAuthError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "LegroomAuthError";
  }
}

export class LegroomCompressError extends LegroomError {
  statusCode: number;
  errorType: string;

  constructor(statusCode: number, errorType: string, message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "LegroomCompressError";
    this.statusCode = statusCode;
    this.errorType = errorType;
  }
}

export class ConfigurationError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "ConfigurationError";
  }
}

export class ProviderError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "ProviderError";
  }
}

export class StorageError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "StorageError";
  }
}

export class TokenizationError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "TokenizationError";
  }
}

export class CacheError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "CacheError";
  }
}

export class ValidationError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "ValidationError";
  }
}

export class TransformError extends LegroomError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, details);
    this.name = "TransformError";
  }
}

// --- Proxy error mapping ---

const ERROR_TYPE_MAP: Record<string, new (message: string, details?: Record<string, any>) => LegroomError> = {
  configuration_error: ConfigurationError,
  provider_error: ProviderError,
  storage_error: StorageError,
  tokenization_error: TokenizationError,
  cache_error: CacheError,
  validation_error: ValidationError,
  transform_error: TransformError,
};

/**
 * Map a proxy error response to the correct LegroomError subclass.
 */
export function mapProxyError(
  status: number,
  type: string,
  message: string,
): LegroomError {
  if (status === 401) return new LegroomAuthError(message);
  const ErrorClass = ERROR_TYPE_MAP[type];
  if (ErrorClass) return new ErrorClass(message, { statusCode: status, errorType: type });
  return new LegroomCompressError(status, type, message);
}
