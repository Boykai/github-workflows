import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.agentprojects.app',
  appName: 'Agent Projects',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    iosScheme: 'https',
  },
  ios: {
    allowsMultipleWindows: false,
    scrollEnabled: true,
    contentInset: 'automatic',
    allowsBackForwardNavigationGestures: true,
  },
  plugins: {
    StatusBar: {
      overlaysWebView: true,
      style: 'Default',
    },
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      backgroundColor: '#ffffff',
      showSpinner: false,
    },
    Keyboard: {
      resize: 'body',
      style: 'Default',
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
  },
};

export default config;
