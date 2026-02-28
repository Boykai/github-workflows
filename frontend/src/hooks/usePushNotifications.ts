/**
 * usePushNotifications — manages APNs push notification registration,
 * permission handling, and notification tap routing on iOS.
 *
 * On web this hook is a no-op.
 *
 * @see specs/014-native-ios-support/contracts/capacitor-plugins.md
 */

import { useEffect, useCallback, useRef } from 'react';
import {
  isNativePlatform,
  getPushNotificationsPlugin,
  getPreferencesPlugin,
} from '@/services/capacitor';

/* ------------------------------------------------------------------ */
/*  Data contract (matches contracts/capacitor-plugins.md)            */
/* ------------------------------------------------------------------ */

export interface IOSPushRegistration {
  permissionStatus: 'granted' | 'denied' | 'prompt';
  deviceToken: string | null;
  registeredAt: string | null;
}

const PUSH_REGISTRATION_KEY = 'ios_push_registration';

/* ------------------------------------------------------------------ */
/*  Hook                                                              */
/* ------------------------------------------------------------------ */

export function usePushNotifications() {
  const initialized = useRef(false);

  const persistRegistration = useCallback(
    async (reg: IOSPushRegistration) => {
      try {
        const Preferences = await getPreferencesPlugin();
        await Preferences.set({
          key: PUSH_REGISTRATION_KEY,
          value: JSON.stringify(reg),
        });
      } catch {
        // non-critical
      }
    },
    [],
  );

  useEffect(() => {
    if (!isNativePlatform() || initialized.current) return;
    initialized.current = true;

    let registrationCleanup: (() => void) | undefined;
    let errorCleanup: (() => void) | undefined;
    let receivedCleanup: (() => void) | undefined;
    let actionCleanup: (() => void) | undefined;

    (async () => {
      try {
        const PushNotifications = await getPushNotificationsPlugin();

        // Check current permission status
        const permResult = await PushNotifications.checkPermissions();

        if (permResult.receive === 'prompt') {
          const reqResult = await PushNotifications.requestPermissions();
          if (reqResult.receive !== 'granted') {
            await persistRegistration({
              permissionStatus: 'denied',
              deviceToken: null,
              registeredAt: null,
            });
            return;
          }
        } else if (permResult.receive !== 'granted') {
          await persistRegistration({
            permissionStatus: 'denied',
            deviceToken: null,
            registeredAt: null,
          });
          return;
        }

        // Register for push notifications
        await PushNotifications.register();

        // Listen for successful registration
        const regHandle = await PushNotifications.addListener(
          'registration',
          async (token) => {
            await persistRegistration({
              permissionStatus: 'granted',
              deviceToken: token.value,
              registeredAt: new Date().toISOString(),
            });
          },
        );
        registrationCleanup = () => regHandle.remove();

        // Listen for registration errors
        const errHandle = await PushNotifications.addListener(
          'registrationError',
          async () => {
            await persistRegistration({
              permissionStatus: 'granted',
              deviceToken: null,
              registeredAt: null,
            });
          },
        );
        errorCleanup = () => errHandle.remove();

        // Handle notifications received while app is in foreground
        const recvHandle = await PushNotifications.addListener(
          'pushNotificationReceived',
          () => {
            // Foreground notification — can show in-app banner if desired
          },
        );
        receivedCleanup = () => recvHandle.remove();

        // Handle notification tap (deep link routing)
        const actionHandle = await PushNotifications.addListener(
          'pushNotificationActionPerformed',
          (action) => {
            const data = action.notification?.data;
            if (data?.route) {
              window.location.hash = data.route as string;
            }
          },
        );
        actionCleanup = () => actionHandle.remove();
      } catch {
        // Plugin not available — running on web
      }
    })();

    return () => {
      registrationCleanup?.();
      errorCleanup?.();
      receivedCleanup?.();
      actionCleanup?.();
    };
  }, [persistRegistration]);
}
