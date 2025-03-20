import { useCallback, useState } from 'react';
import { useApiRequest } from './useApiRequest';

interface UploadOptions {
  maxFileSize?: number; // in bytes
  allowedTypes?: string[];
  onProgress?: (progress: number) => void;
  onSuccess?: (response: any) => void;
  onError?: (error: Error) => void;
}

interface UploadState {
  progress: number;
  isUploading: boolean;
  error: Error | null;
  file: File | null;
}

export const useFileUpload = (options: UploadOptions = {}) => {
  const {
    maxFileSize = 10 * 1024 * 1024, // 10MB
    allowedTypes = [],
    onProgress,
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<UploadState>({
    progress: 0,
    isUploading: false,
    error: null,
    file: null,
  });

  const { execute } = useApiRequest();

  const validateFile = useCallback(
    (file: File): string | null => {
      if (file.size > maxFileSize) {
        return `File size exceeds ${maxFileSize / (1024 * 1024)}MB limit`;
      }

      if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
        return `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`;
      }

      return null;
    },
    [maxFileSize, allowedTypes]
  );

  const uploadFile = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        const error = new Error(validationError);
        setState((prev) => ({
          ...prev,
          error,
          isUploading: false,
        }));
        onError?.(error);
        return;
      }

      setState((prev) => ({
        ...prev,
        file,
        progress: 0,
        isUploading: true,
        error: null,
      }));

      const formData = new FormData();
      formData.append('file', file);

      try {
        const result = await execute(
          async () => {
            const xhr = new XMLHttpRequest();
            return new Promise((resolve, reject) => {
              xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                  const progress = (event.loaded / event.total) * 100;
                  setState((prev) => ({
                    ...prev,
                    progress,
                  }));
                  onProgress?.(progress);
                }
              });

              xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                  resolve(JSON.parse(xhr.response));
                } else {
                  reject(new Error(`Upload failed with status ${xhr.status}`));
                }
              });

              xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
              });

              xhr.open('POST', '/api/upload');
              xhr.send(formData);
            });
          },
          {
            onSuccess: (response) => {
              setState((prev) => ({
                ...prev,
                progress: 100,
                isUploading: false,
              }));
              onSuccess?.(response);
            },
            onError: (error) => {
              setState((prev) => ({
                ...prev,
                error,
                isUploading: false,
              }));
              onError?.(error);
            },
          }
        );

        return result;
      } catch (error) {
        const errorObj = error instanceof Error ? error : new Error('Upload failed');
        setState((prev) => ({
          ...prev,
          error: errorObj,
          isUploading: false,
        }));
        onError?.(errorObj);
      }
    },
    [execute, validateFile, onProgress, onSuccess, onError]
  );

  const cancelUpload = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isUploading: false,
      progress: 0,
      error: null,
      file: null,
    }));
  }, []);

  const resetState = useCallback(() => {
    setState({
      progress: 0,
      isUploading: false,
      error: null,
      file: null,
    });
  }, []);

  return {
    ...state,
    uploadFile,
    cancelUpload,
    resetState,
  };
}; 