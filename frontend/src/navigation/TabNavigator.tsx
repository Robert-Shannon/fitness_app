import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import HomeScreen from '../screens/dashboard/HomeScreen';
import { ProfileScreen } from '../screens/dashboard/ProfileScreen';
import { WorkoutsScreen } from '../screens/whoop/WorkoutsScreen';
import { SleepScreen } from '../screens/whoop/SleepScreen';
import { RecoveryScreen } from '../screens/whoop/RecoveryScreen';

export type TabParamList = {
  Home: undefined;
  Workouts: undefined;
  Sleep: undefined;
  Recovery: undefined;
  Profile: undefined;
};

const Tab = createBottomTabNavigator<TabParamList>();

const TabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Ionicons.glyphMap;

          switch (route.name) {
            case 'Home':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Workouts':
              iconName = focused ? 'fitness' : 'fitness-outline';
              break;
            case 'Sleep':
              iconName = focused ? 'moon' : 'moon-outline';
              break;
            case 'Recovery':
              iconName = focused ? 'refresh-circle' : 'refresh-circle-outline';
              break;
            case 'Profile':
              iconName = focused ? 'person' : 'person-outline';
              break;
            default:
              iconName = 'home-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: 'gray',
        headerShown: true,
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{
          title: 'Dashboard'
        }}
      />
      <Tab.Screen 
        name="Workouts" 
        component={WorkoutsScreen}
      />
      <Tab.Screen 
        name="Sleep" 
        component={SleepScreen}
      />
      <Tab.Screen 
        name="Recovery" 
        component={RecoveryScreen}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
      />
    </Tab.Navigator>
  );
};

export default TabNavigator;