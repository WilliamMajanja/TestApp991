# PowerSync + Supabase Integration Demo

A proof-of-concept React application demonstrating offline-first data synchronization between a mobile frontend and Supabase backend using PowerSync.

## 🚀 Project Overview

This project showcases the integration of [PowerSync](https://powersync.com) with [Supabase](https://supabase.com) to create an offline-first todo list application. The app demonstrates:

- **Offline-first functionality**: Works seamlessly without internet connection
- **Real-time synchronization**: Automatic sync when connectivity is restored
- **Local SQLite storage**: PowerSync manages local data with SQLite
- **Conflict resolution**: Handles data conflicts during synchronization
- **React integration**: Uses PowerSync React SDK for reactive data operations

## 🛠 Tech Stack

- **Frontend**: React 19, PowerSync React SDK, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **Database**: Supabase (PostgreSQL), PowerSync (SQLite for local storage)
- **Synchronization**: PowerSync Cloud Service
- **Authentication**: Supabase Auth (ready for implementation)

## 📋 Features

- ✅ Create and manage todo lists
- ✅ Add, edit, and toggle todos
- ✅ Offline-first data operations
- ✅ Local data persistence with SQLite
- ✅ Real-time sync status indicators
- ✅ Responsive design with Tailwind CSS
- ✅ Error handling and graceful degradation

## 🏗 Project Structure

```
/app/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main FastAPI application
│   ├── setup_supabase.py   # Database setup script (manual)
│   ├── setup_supabase_simple.py  # Simple setup instructions
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Backend environment variables
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component with PowerSync
│   │   ├── App.css        # Application styles
│   │   └── index.js       # React entry point
│   ├── package.json       # Node.js dependencies
│   └── .env              # Frontend environment variables
└── README.md              # This file
```

## 🔧 Setup Instructions

### 1. Prerequisites

- Node.js 18+ and Yarn
- Python 3.11+
- A Supabase account and project
- A PowerSync account (free tier available)

### 2. Supabase Setup

1. **Create a Supabase project** at https://supabase.com
2. **Get your project credentials**:
   - Go to Project Settings → API
   - Note your Project URL and anon key
   - Note your service_role key

3. **Create database schema** by running this SQL in your Supabase SQL Editor:

```sql
-- Create tables
CREATE TABLE IF NOT EXISTS lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID REFERENCES lists(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert sample data
INSERT INTO lists (name) VALUES 
('My First List'),
('Work Tasks'),
('Personal Goals');

INSERT INTO todos (list_id, description, completed) 
SELECT 
    (SELECT id FROM lists LIMIT 1),
    description,
    false
FROM (VALUES 
    ('Set up PowerSync integration'),
    ('Test offline synchronization'),
    ('Build React UI')
) AS t(description);

-- Enable Row Level Security
ALTER TABLE lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE todos ENABLE ROW LEVEL SECURITY;

-- Create policies for demo (allows all operations)
CREATE POLICY lists_policy ON lists FOR ALL USING (true);
CREATE POLICY todos_policy ON todos FOR ALL USING (true);
```

4. **Set up PowerSync replication** (requires database admin privileges):

```sql
-- Create PowerSync role
CREATE ROLE powersync_role WITH REPLICATION BYPASSRLS LOGIN PASSWORD 'your_secure_password';
GRANT USAGE ON SCHEMA public TO powersync_role;
GRANT SELECT ON lists, todos TO powersync_role;

-- Create publication
CREATE PUBLICATION powersync FOR TABLE lists, todos;
```

### 3. PowerSync Cloud Setup

1. **Create a PowerSync account** at https://app.powersync.com
2. **Create a new PowerSync instance**:
   - Give it a name (e.g., "Todo Demo")
   - Choose your preferred region
3. **Configure database connection**:
   - Use your Supabase database URL
   - Use the `powersync_role` credentials
4. **Set up sync rules**:

```yaml
bucket_definitions:
  global_data:
    data:
      - SELECT * FROM lists
      - SELECT * FROM todos
```

5. **Get your PowerSync instance URL** (wss://your-instance.powersync.com)

### 4. Environment Configuration

Update your environment files with your credentials:

**Backend (.env):**
```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

**Frontend (.env):**
```env
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
REACT_APP_POWERSYNC_URL=wss://your-instance.powersync.com
```

### 5. Installation and Running

1. **Install backend dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Install frontend dependencies**:
```bash
cd frontend
yarn install
```

3. **Start the application**:
```bash
# From the root directory
sudo supervisorctl restart all
```

The application will be available at your frontend URL.

## 🧪 Testing

### Backend API Testing

Test the backend APIs:
```bash
cd backend
python backend_test.py
```

### Frontend Testing

The app includes comprehensive error handling and works in offline mode even without a complete PowerSync setup.

## 🔄 How PowerSync Works

### Offline-First Architecture

1. **Local SQLite Database**: PowerSync maintains a local SQLite database in the browser
2. **Automatic Sync**: Changes are automatically synced to Supabase when online
3. **Conflict Resolution**: PowerSync handles conflicts using last-write-wins strategy
4. **Real-time Updates**: Changes from other clients are pushed in real-time

### Data Flow

```
React App ↔ PowerSync SQLite ↔ PowerSync Cloud ↔ Supabase PostgreSQL
```

### Key Components

- **PowerSyncDatabase**: Local SQLite database with sync capabilities
- **Connector**: Handles authentication and data upload to Supabase
- **Sync Rules**: Define what data to sync and how to partition it
- **React Hooks**: `usePowerSync`, `useQuery` for reactive data operations

## 🎯 Usage

### Creating Lists
```javascript
await powerSync.execute(
  'INSERT INTO lists (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)',
  [id, name, now, now]
);
```

### Adding Todos
```javascript
await powerSync.execute(
  'INSERT INTO todos (id, list_id, description, completed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
  [id, listId, description, false, now, now]
);
```

### Querying Data
```javascript
const lists = await powerSync.getAll('SELECT * FROM lists ORDER BY created_at DESC');
```

## 🚨 Troubleshooting

### Common Issues

1. **PowerSync initialization fails**:
   - Ensure all dependencies are installed: `@powersync/web`, `@powersync/react`, `@journeyapps/wa-sqlite`
   - Check browser console for detailed error messages

2. **Supabase connection errors**:
   - Verify your environment variables are correct
   - Ensure database tables are created
   - Check Row Level Security policies

3. **Sync not working**:
   - Verify PowerSync instance configuration
   - Check sync rules in PowerSync dashboard
   - Ensure database publication is created correctly

### Debug Mode

Enable debug logging by adding to your React app:
```javascript
// Enable PowerSync debug logging
localStorage.setItem('powersync-log-level', 'debug');
```

## 🔐 Security Considerations

For production use, implement:

- **Row Level Security (RLS)**: Proper access control in Supabase
- **Authentication**: User authentication with Supabase Auth
- **Sync Rules**: User-specific data partitioning
- **Environment Variables**: Secure API key management

## 📦 Dependencies

### Backend
- FastAPI 0.110.1
- Supabase Python client 2.0.0+
- psycopg2-binary 2.9.0+

### Frontend
- React 19.0.0
- @powersync/web 1.22.0
- @powersync/react 1.5.3
- @supabase/supabase-js 2.50.0
- @journeyapps/wa-sqlite (for SQLite support)

## 🚀 Next Steps

To extend this demo:

1. **Add Authentication**: Implement user authentication with Supabase Auth
2. **User-specific Data**: Update sync rules for user-specific data partitioning
3. **Conflict Resolution**: Implement custom conflict resolution strategies
4. **File Attachments**: Add support for file uploads and sync
5. **Push Notifications**: Implement real-time notifications
6. **Mobile App**: Create React Native version using the same PowerSync setup

## 📚 Resources

- [PowerSync Documentation](https://docs.powersync.com/)
- [PowerSync + Supabase Guide](https://docs.powersync.com/integration-guides/supabase-+-powersync)
- [Supabase Documentation](https://supabase.com/docs)
- [PowerSync React SDK](https://docs.powersync.com/client-sdk-references/react)

## 🤝 Contributing

This is a proof-of-concept demo. For production use, consider:
- Adding comprehensive error handling
- Implementing proper authentication
- Adding unit and integration tests
- Setting up CI/CD pipelines
- Adding monitoring and analytics

## 📄 License

This project is for demonstration purposes. Please refer to PowerSync and Supabase licensing for production use.

---

**Built with ❤️ using PowerSync + Supabase**

For questions or issues, please check the troubleshooting section or refer to the official documentation.
