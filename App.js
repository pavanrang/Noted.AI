import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StyleSheet, View, Text, TextInput, TouchableOpacity, SafeAreaView, FlatList, Alert } from 'react-native';
import { Audio } from 'expo-av';
import * as DocumentPicker from 'expo-document-picker';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import Groq from 'groq-sdk';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const GROQ_API_KEY = '';
const groq = new Groq({ apiKey: GROQ_API_KEY, dangerouslyAllowBrowser: true });

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#8E6CEF',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    borderWidth: 1,
    borderColor: '#8E6CEF',
    borderRadius: 5,
    padding: 10,
    marginBottom: 10,
  },
  
  button: {
    backgroundColor: '#8E6CEF',
    padding: 15,
    borderRadius: 5,
    alignItems: 'center',
    marginVertical: 10,
  },
  buttonText: {
    color: '#ffffff',
    fontWeight: 'bold',
  },
  recordButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#8E6CEF',
    justifyContent: 'center',
    alignItems: 'center',
    alignSelf: 'center',
    marginBottom: 20,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 5,
    padding: 15,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  listItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  editInput: {
    borderWidth: 1,
    borderColor: '#8E6CEF',
    borderRadius: 5,
    padding: 10,
    marginBottom: 10,
  },
});

const SignInScreen = ({ navigation }) => {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Audio Analyzer</Text>
      <TextInput style={styles.input} placeholder="Email" />
      <TextInput style={styles.input} placeholder="Password" secureTextEntry />
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate('MainTabs')}
      >
        <Text style={styles.buttonText}>Sign In</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
};

const RecordScreen = ({ navigation }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recording, setRecording] = useState(null);

  const startRecording = async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      const { recording } = await Audio.Recording.createAsync(
        Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
      );
      setRecording(recording);
      setIsRecording(true);
    } catch (err) {
      console.error('Failed to start recording', err);
    }
  };

  const stopRecording = async () => {
    setIsRecording(false);
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    console.log('Recording stopped and stored at', uri);
    navigation.navigate('Transcription', { 
      uri,
      fileName: `Recording_${new Date().toISOString().split('T')[0]}`
    });
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Record Audio</Text>
      <TouchableOpacity style={styles.recordButton} onPress={toggleRecording}>
        <Ionicons
          name={isRecording ? 'stop' : 'mic'}
          size={50}
          color="#ffffff"
        />
      </TouchableOpacity>
      <Text style={{textAlign: 'center', marginBottom: 20}}>
        {isRecording ? 'Recording...' : 'Tap to start recording'}
      </Text>
    </View>
  );
};

const UploadScreen = ({ navigation }) => {
  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'audio/*',
      });
      if (result.assets && result.assets.length > 0) {
        console.log('Uploaded file:', result.assets[0].name);
        navigation.navigate('Transcription', { 
          uri: result.assets[0].uri,
          fileName: result.assets[0].name
        });
      }
    } catch (err) {
      console.log('Error picking document:', err);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Upload Audio</Text>
      <TouchableOpacity style={styles.button} onPress={pickDocument}>
        <Text style={styles.buttonText}>Choose File</Text>
      </TouchableOpacity>
    </View>
  );
};

const TranscriptionScreen = ({ route, navigation }) => {
  const [transcript, setTranscript] = useState('');
  const [summary, setSummary] = useState('');
  const [sound, setSound] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const { uri, fileName } = route.params;

  useEffect(() => {
    return sound
      ? () => {
          console.log('Unloading Sound');
          sound.unloadAsync();
        }
      : undefined;
  }, [sound]);

  const playPauseAudio = async () => {
    if (sound) {
      if (isPlaying) {
        await sound.pauseAsync();
      } else {
        await sound.playAsync();
      }
      setIsPlaying(!isPlaying);
    } else {
      const { sound: newSound } = await Audio.Sound.createAsync({ uri });
      setSound(newSound);
      await newSound.playAsync();
      setIsPlaying(true);
    }
  };

  const transcribeAudio = async () => {
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: uri,
        name: 'audio.mp3',
        type: 'audio/mpeg'
      });
      formData.append('model', 'whisper-large-v3');
      formData.append('response_format', 'json');

      const response = await axios.post('https://api.groq.com/openai/v1/audio/transcriptions', formData, {
        headers: {
          'Authorization': `Bearer ${GROQ_API_KEY}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      setTranscript(response.data.text);
      
      // Generate summary
      const summaryText = await summarizeTranscript(response.data.text);
      setSummary(summaryText);
    } catch (error) {
      console.error('Transcription error:', error);
    }
  };

  const summarizeTranscript = async (transcriptText) => {
    try {
      const chatCompletion = await groq.chat.completions.create({
        messages: [
          { role: 'system', content: 'You are a helpful assistant that summarizes transcripts.' },
          { role: 'user', content: `Please summarize the following transcript:\n\n${transcriptText}` }
        ],
        model: 'llama3-8b-8192',
      });
      return chatCompletion.choices[0].message.content;
    } catch (error) {
      console.error('Error summarizing transcript:', error);
      return 'Failed to generate summary.';
    }
  };

  const saveTranscript = async () => {
    const newTranscript = { 
      id: Date.now().toString(), 
      title: fileName || 'Unnamed Recording', 
      date: new Date().toISOString().split('T')[0], 
      content: transcript,
      summary: summary,
      audioUri: uri
    };

    // Save audio file to app's documents directory
    const audioFileInfo = await FileSystem.getInfoAsync(uri);
    if (audioFileInfo.exists) {
      const newAudioUri = FileSystem.documentDirectory + fileName;
      await FileSystem.copyAsync({
        from: uri,
        to: newAudioUri
      });
      newTranscript.audioUri = newAudioUri;
    }

    navigation.navigate('Recordings', { newTranscript });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Transcription</Text>
      <Text style={{marginBottom: 10}}>{fileName || 'Unnamed Recording'}</Text>
      <TouchableOpacity style={styles.button} onPress={playPauseAudio}>
        <Text style={styles.buttonText}>{isPlaying ? "Pause" : "Play"}</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.button} onPress={transcribeAudio}>
        <Text style={styles.buttonText}>Generate Transcript</Text>
      </TouchableOpacity>
      <View style={styles.card}>
        <TextInput
          multiline
          numberOfLines={10}
          onChangeText={setTranscript}
          value={transcript}
          style={{textAlignVertical: 'top'}}
        />
      </View>
      <TouchableOpacity style={styles.button} onPress={saveTranscript}>
        <Text style={styles.buttonText}>Save</Text>
      </TouchableOpacity>
    </View>
  );
};

const RecordingsScreen = ({ route, navigation }) => {
  const [recordings, setRecordings] = useState([
    { id: '1', title: 'Meeting Notes', date: '2023-09-15', content: 'Content of meeting notes...', summary: 'Summary of meeting notes...', audioUri: '' },
    { id: '2', title: 'Interview', date: '2023-09-14', content: 'Content of interview...', summary: 'Summary of interview...', audioUri: '' },
    { id: '3', title: 'Lecture', date: '2023-09-13', content: 'Content of lecture...', summary: 'Summary of lecture...', audioUri: '' },
  ]);

  useEffect(() => {
    if (route.params?.newTranscript) {
      setRecordings(prevRecordings => [route.params.newTranscript, ...prevRecordings]);
    }
    if (route.params?.updatedTranscript) {
      setRecordings(prevRecordings => 
        prevRecordings.map(recording => 
          recording.id === route.params.updatedTranscript.id ? route.params.updatedTranscript : recording
        )
      );
    }
  }, [route.params?.newTranscript, route.params?.updatedTranscript]);

  const deleteRecording = (id) => {
    Alert.alert(
      "Delete Recording",
      "Are you sure you want to delete this recording?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Delete", onPress: () => {
          setRecordings(prevRecordings => prevRecordings.filter(recording => recording.id !== id));
        }}
      ]
    );
  };

  const renderItem = ({ item }) => (
    <View style={styles.listItem}>
      <TouchableOpacity onPress={() => navigation.navigate('TranscriptDetail', { transcript: item })}>
        <View>
          <Text style={{fontWeight: 'bold'}}>{item.title}</Text>
          <Text style={{color: 'gray'}}>{item.date}</Text>
        </View>
      </TouchableOpacity>
      <View style={{flexDirection: 'row'}}>
        <TouchableOpacity onPress={() => navigation.navigate('EditRecording', { transcript: item })}>
          <Ionicons name="create-outline" size={24} color="#8E6CEF" style={{marginRight: 15}} />
        </TouchableOpacity>
        <TouchableOpacity onPress={() => deleteRecording(item.id)}>
          <Ionicons name="trash-outline" size={24} color="#FF6B6B" />
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>My Recordings</Text>
      <FlatList
        data={recordings}
        renderItem={renderItem}
        keyExtractor={item => item.id}
      />
    </View>
  );
};

const EditRecordingScreen = ({ route, navigation }) => {
  const { transcript } = route.params;
  const [title, setTitle] = useState(transcript.title);
  const [content, setContent] = useState(transcript.content);
  const [summary, setSummary] = useState(transcript.summary);

  const saveChanges = () => {
    const updatedTranscript = {
      ...transcript,
      title,
      content,
      summary,
    };
    navigation.navigate('Recordings', { updatedTranscript });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Edit Recording</Text>
      <TextInput
        style={styles.editInput}
        value={title}
        onChangeText={setTitle}
        placeholder="Title"
      />
      <TextInput
        style={[styles.editInput, { height: 100 }]}
        value={summary}
        onChangeText={setSummary}
        placeholder="Summary"
        multiline
      />
      <TextInput
        style={[styles.editInput, { height: 200 }]}
        value={content}
        onChangeText={setContent}
        placeholder="Transcript"
        multiline
      />
      <TouchableOpacity style={styles.button} onPress={saveChanges}>
        <Text style={styles.buttonText}>Save Changes</Text>
      </TouchableOpacity>
    </View>
  );
};


const TranscriptDetailScreen = ({ route, navigation }) => {
  const { transcript } = route.params;
  const [sound, setSound] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    return sound
      ? () => {
          console.log('Unloading Sound');
          sound.unloadAsync();
        }
      : undefined;
  }, [sound]);

  const playPauseAudio = async () => {
    if (sound) {
      if (isPlaying) {
        await sound.pauseAsync();
      } else {
        await sound.playAsync();
      }
      setIsPlaying(!isPlaying);
    } else {
      const { sound: newSound } = await Audio.Sound.createAsync({ uri: transcript.audioUri });
      setSound(newSound);
      await newSound.playAsync();
      setIsPlaying(true);
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity 
        style={styles.button} 
        onPress={() => navigation.goBack()}
      >
        <Text style={styles.buttonText}>Back to Recordings</Text>
      </TouchableOpacity>
      <Text style={styles.title}>{transcript.title}</Text>
      <Text style={{marginBottom: 10, color: 'gray'}}>{transcript.date}</Text>
      <TouchableOpacity style={styles.button} onPress={playPauseAudio}>
        <Text style={styles.buttonText}>{isPlaying ? "Pause" : "Play"}</Text>
      </TouchableOpacity>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Summary</Text>
        <Text>{transcript.summary}</Text>
      </View>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Transcript</Text>
        <Text>{transcript.content}</Text>
      </View>
    </View>
  );
};

const MainTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Record') {
            iconName = focused ? 'mic' : 'mic-outline';
          } else if (route.name === 'Upload') {
            iconName = focused ? 'cloud-upload' : 'cloud-upload-outline';
          } else if (route.name === 'Recordings') {
            iconName = focused ? 'list' : 'list-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
      tabBarOptions={{
        activeTintColor: '#8E6CEF',
        inactiveTintColor: 'gray',
      }}
    >
      <Tab.Screen name="Record" component={RecordScreen} />
      <Tab.Screen name="Upload" component={UploadScreen} />
      <Tab.Screen name="Recordings" component={RecordingsScreen} />
    </Tab.Navigator>
  );
};

const MainStackNavigator = () => {
  return (
    <Stack.Navigator>
      <Stack.Screen 
        name="MainTabs" 
        component={MainTabs} 
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="Transcription" 
        component={TranscriptionScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="TranscriptDetail" 
        component={TranscriptDetailScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="EditRecording" 
        component={EditRecordingScreen}
        options={{ headerShown: false }}
      />
    </Stack.Navigator>
  );
};

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="SignIn" component={SignInScreen} />
        <Stack.Screen name="MainTabs" component={MainStackNavigator} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}