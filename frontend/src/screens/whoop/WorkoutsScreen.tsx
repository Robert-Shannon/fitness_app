// src/screens/whoop/WorkoutsScreen.tsx
import { View, Text, StyleSheet } from 'react-native';

export const WorkoutsScreen: React.FC = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Workouts Screen</Text>
      <Text style={styles.subtext}>Under Development</Text>
    </View>
  );
};

// Shared styles
const styles = StyleSheet.create({
    container: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: '#f5f5f5',
    },
    text: {
      fontSize: 24,
      fontWeight: 'bold',
      marginBottom: 10,
    },
    subtext: {
      fontSize: 16,
      color: '#666',
    },
  });