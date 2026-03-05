/**
 * Hook for voice input using Web Speech API.
 * Wraps SpeechRecognition/webkitSpeechRecognition with recording state,
 * interim/final transcription, browser support detection, and permission handling.
 */

import { useState, useCallback, useRef, useEffect } from 'react';

type VoiceRecordingState = 'idle' | 'recording' | 'processing' | 'error';

interface UseVoiceInputReturn {
  isRecording: boolean;
  isSupported: boolean;
  recordingState: VoiceRecordingState;
  transcribedText: string;
  interimText: string;
  error: string | null;
  startRecording: () => void;
  stopRecording: () => void;
  toggleRecording: () => void;
  clearTranscription: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionInstance = any;

// Check browser support
function getSpeechRecognitionCtor(): (new () => SpeechRecognitionInstance) | null {
  if (typeof window === 'undefined') return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  return SR || null;
}

export function useVoiceInput(): UseVoiceInputReturn {
  const [recordingState, setRecordingState] = useState<VoiceRecordingState>('idle');
  const [transcribedText, setTranscribedText] = useState('');
  const [interimText, setInterimText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const isSupported = getSpeechRecognitionCtor() !== null;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ignore errors during cleanup
        }
        recognitionRef.current = null;
      }
    };
  }, []);

  const startRecording = useCallback(() => {
    const SpeechRecognitionCtor = getSpeechRecognitionCtor();
    if (!SpeechRecognitionCtor) {
      setError('Voice input is not supported in this browser. Try Chrome or Edge.');
      setRecordingState('error');
      return;
    }

    setError(null);
    setInterimText('');

    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setRecordingState('recording');
    };

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      if (finalTranscript) {
        setTranscribedText((prev) => prev + finalTranscript);
        setInterimText('');
      } else {
        setInterimText(interimTranscript);
      }
    };

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onerror = (event: any) => {
      if (event.error === 'not-allowed') {
        setError(
          'Microphone access denied. Please enable microphone permissions in your browser settings.'
        );
      } else if (event.error === 'no-speech') {
        // Not a real error - just no speech detected
        return;
      } else {
        setError(`Voice input error: ${event.error}`);
      }
      setRecordingState('error');
      recognitionRef.current = null;
    };

    recognition.onend = () => {
      // Always transition to idle when recognition ends, unless an error
      // already set the state (onerror fires before onend).
      setRecordingState((prev) => (prev === 'error' ? prev : 'idle'));
      setInterimText('');
      recognitionRef.current = null;
    };

    try {
      recognition.start();
      recognitionRef.current = recognition;
    } catch {
      setError('Failed to start voice recording. Please try again.');
      setRecordingState('error');
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      setRecordingState('processing');
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore errors during stop
      }
    }
  }, []);

  const toggleRecording = useCallback(() => {
    if (recordingState === 'recording') {
      stopRecording();
    } else {
      startRecording();
    }
  }, [recordingState, startRecording, stopRecording]);

  const clearTranscription = useCallback(() => {
    setTranscribedText('');
    setInterimText('');
    setError(null);
    if (recordingState === 'error') {
      setRecordingState('idle');
    }
  }, [recordingState]);

  return {
    isRecording: recordingState === 'recording',
    isSupported,
    recordingState,
    transcribedText,
    interimText,
    error,
    startRecording,
    stopRecording,
    toggleRecording,
    clearTranscription,
  };
}
