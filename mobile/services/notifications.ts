/**
 * Push notification service using Expo Notifications.
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { api } from './api';

export async function registerForPushNotifications(): Promise<string | null> {
  // Push notifications don't work in Expo Go for SDK 53+
  // Need a development build for full functionality
  if (!Device.isDevice) {
    console.log('Push notifications only work on physical devices');
    return null;
  }

  try {
    // Check existing permissions
    const { status: existingStatus } =
      await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    // Request permission if not granted
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Push notification permission denied');
      return null;
    }

    // Get push token - this fails in Expo Go for SDK 53+
    let token: string;
    try {
      token = (await Notifications.getExpoPushTokenAsync({
        projectId: 'dealscout-88ed6',
      })).data;
      console.log('Push token:', token);
    } catch (e) {
      console.log('Push tokens not available in Expo Go (SDK 53+). Use a dev build.');
      return null;
    }

    // Register with backend
    try {
      await api.registerDeviceToken(token);
      console.log('Token registered with backend');
    } catch (error) {
      console.error('Failed to register token with backend:', error);
    }

    // Android-specific channel setup
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('deals', {
        name: 'Deal Alerts',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#4ecca3',
      });

      await Notifications.setNotificationChannelAsync('review', {
        name: 'Items to Review',
        importance: Notifications.AndroidImportance.DEFAULT,
      });
    }

    return token;
  } catch (error) {
    console.log('Push notifications not available:', error);
    return null;
  }
}

export async function scheduleDemoNotification(): Promise<void> {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: '$45 Profit Opportunity',
      body: 'RTX 3080 Graphics Card - Facebook Marketplace',
      data: { type: 'deal', deal_id: '1' },
    },
    trigger: { seconds: 2 },
  });
}
