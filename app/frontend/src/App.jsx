import { useState } from 'react';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import axios from 'axios';

export default function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // This component handles the entire Login/Signup flow automatically
  return (
    <Authenticator>
      {({ signOut, user }) => (
        <div style={{ padding: '50px' }}>
          <h1>📚 AWS Study Buddy</h1>
          <p>Welcome, {user.username}</p>
          <button onClick={signOut}>Sign out</button>

          <hr />

          <h3>1. Upload Document</h3>
          <input type="file" onChange={(e) => setFile(e.target.files[0])} />
          <button onClick={() => uploadFile(file, user, setLoading, setMessage)} disabled={loading}>
            {loading ? 'Processing...' : 'Process PDF'}
          </button>
          {message && <p>{message}</p>}
        </div>
      )}
    </Authenticator>
  );
}

async function uploadFile(file, user, setLoading, setMessage) {
  if (!file) {
    setMessage('Please select a file to upload.');
    return;
  }

  setLoading(true);
  setMessage('');

  try {
    // 1. Get the JWT Token from the current session
    const session = await user.getSession();
    const token = session.getIdToken().getJwtToken();

    // 2. Ask Backend for Presigned URL
    const res = await axios.post('/api/upload',
      {
        filename: file.name,
        mode: "audio"
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    // 3. Upload directly to S3
    const { upload_url } = res.data;
    await axios.put(upload_url, file, {
      headers: { 'Content-Type': file.type }
    });

    setMessage("File Uploaded! Check back in 5 minutes.");

  } catch (err) {
    console.error(err);
    setMessage("Upload failed. Please try again.");
  } finally {
    setLoading(false);
  }
}
