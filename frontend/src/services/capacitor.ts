/**
 * Capacitor platform detection and plugin initialization utilities.
 * Provides graceful degradation on web — all helpers are safe to call
 * regardless of whether the app is running in a native shell or a browser.
 */

import { Capacitor } from '@capacitor/core';

/** Returns true when running inside a native Capacitor shell (iOS/Android). */
export function isNativePlatform(): boolean {
  return Capacitor.isNativePlatform();
}

/** Returns true when running on iOS (native Capacitor shell). */
export function isIOS(): boolean {
  return Capacitor.getPlatform() === 'ios';
}

/** Returns the current platform identifier ('ios', 'android', or 'web'). */
export function getPlatform(): string {
  return Capacitor.getPlatform();
}

/* ------------------------------------------------------------------ */
/*  Lazy plugin imports — each function dynamically imports its plugin */
/*  so tree-shaking removes unused plugins on web builds.             */
/* ------------------------------------------------------------------ */

export async function getAppPlugin() {
  const { App } = await import('@capacitor/app');
  return App;
}

export async function getStatusBarPlugin() {
  const { StatusBar } = await import('@capacitor/status-bar');
  return StatusBar;
}

export async function getSplashScreenPlugin() {
  const { SplashScreen } = await import('@capacitor/splash-screen');
  return SplashScreen;
}

export async function getKeyboardPlugin() {
  const { Keyboard } = await import('@capacitor/keyboard');
  return Keyboard;
}

export async function getPushNotificationsPlugin() {
  const { PushNotifications } = await import('@capacitor/push-notifications');
  return PushNotifications;
}

export async function getPreferencesPlugin() {
  const { Preferences } = await import('@capacitor/preferences');
  return Preferences;
}
