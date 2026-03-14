/**
 * useVoiceInput — encapsulates Web Speech API integration,
 * permission handling, and transcription state.
 */

import { useState, useCallback, useRef, useEffect } from 'react';

interface UseVoiceInputReturn {
  isSupported: boolean;
  isRecording: boolean;
  interimTranscript: string;
  error: string | null;
  startRecording: () => void;
  stopRecording: () => void;
  cancelRecording: () => void;
}

// Augment Window for Web Speech API
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message?: string;
}

type SpeechRecognitionInstance = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
};

function getSpeechRecognitionConstructor(): (new () => SpeechRecognitionInstance) | null {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const win = window as any;
  return win.SpeechRecognition || win.webkitSpeechRecognition || null;
}

export function useVoiceInput(onTranscript: (text: string) => void): UseVoiceInputReturn {
  const [isSupported] = useState(() => getSpeechRecognitionConstructor() !== null);
  const [isRecording, setIsRecording] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
        recognitionRef.current = null;
      }
    };
  }, []);

  const startRecording = useCallback(() => {
    const SpeechRecognitionCtor = getSpeechRecognitionConstructor();
    if (!SpeechRecognitionCtor) {
      setError('Voice input is not supported in this browser.');
      return;
    }

    setError(null);
    setInterimTranscript('');

    // Request microphone permission first
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          // Stop the stream immediately — we just needed permission
          stream.getTracks().forEach((track) => track.stop());

          const recognition = new SpeechRecognitionCtor();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';

          recognition.onresult = (event: SpeechRecognitionEvent) => {
            let interim = '';
            let finalText = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
              const transcript = event.results[i][0].transcript;
              if (event.results[i].isFinal) {
                finalText += transcript;
              } else {
                interim += transcript;
              }
            }

            setInterimTranscript(interim);
            if (finalText) {
              onTranscript(finalText);
            }
          };

          recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            if (event.error === 'not-allowed' || event.error === 'permission-denied') {
              setError(
                'Microphone access is required for voice input. Please allow microphone access in your browser settings.'
              );
            } else if (event.error !== 'aborted') {
              setError(`Voice input error: ${event.error}`);
            }
            setIsRecording(false);
          };

          recognition.onend = () => {
            setIsRecording(false);
            setInterimTranscript('');
          };

          recognitionRef.current = recognition;
          recognition.start();
          setIsRecording(true);
        })
        .catch(() => {
          setError(
            'Microphone access is required for voice input. Please allow microphone access in your browser settings.'
          );
        });
    } else {
      setError('Microphone access is not available in this browser.');
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsRecording(false);
  }, []);

  const cancelRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }
    setIsRecording(false);
    setInterimTranscript('');
  }, []);

  return {
    isSupported,
    isRecording,
    interimTranscript,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
