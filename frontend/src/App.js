import React, { useState, useEffect } from 'react';
import { PowerSyncDatabase } from '@powersync/web';
import { PowerSyncContext } from '@powersync/react';
import { createClient } from '@supabase/supabase-js';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

// Supabase configuration
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

console.log('Supabase URL:', supabaseUrl);
console.log('Supabase Key:', supabaseAnonKey ? 'Present' : 'Missing');

const supabase = createClient(supabaseUrl, supabaseAnonKey);

// SQLite schema for local storage
const schema = [
  `CREATE TABLE IF NOT EXISTS lists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT
  )`,
  `CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,
    list_id TEXT NOT NULL,
    description TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (list_id) REFERENCES lists(id)
  )`
];

// Initialize PowerSync database
const powerSync = new PowerSyncDatabase({
  database: {
    dbName: 'powersync-demo.db',
    schema: schema
  },
  flags: {
    enableMultiTabs: false
  }
});

// PowerSync Connector for Supabase
class SupabaseConnector {
  async fetchCredentials() {
    // For demo purposes, we'll use a mock token
    // In production, this would be a real auth token
    return {
      endpoint: 'wss://mock-powersync-endpoint.com', // This will be replaced with real PowerSync endpoint
      token: 'mock-token'
    };
  }

  async uploadData(database) {
    const transaction = await database.getNextCrudTransaction();
    
    if (!transaction) {
      return;
    }

    try {
      for (const op of transaction.crud) {
        console.log('Syncing operation:', op);
        
        switch (op.op) {
          case 'PUT':
            if (op.table === 'lists') {
              await supabase.from('lists').upsert(op.opData);
            } else if (op.table === 'todos') {
              await supabase.from('todos').upsert(op.opData);
            }
            break;
          case 'PATCH':
            if (op.table === 'lists') {
              await supabase.from('lists').update(op.opData).eq('id', op.id);
            } else if (op.table === 'todos') {
              await supabase.from('todos').update(op.opData).eq('id', op.id);
            }
            break;
          case 'DELETE':
            if (op.table === 'lists') {
              await supabase.from('lists').delete().eq('id', op.id);
            } else if (op.table === 'todos') {
              await supabase.from('todos').delete().eq('id', op.id);
            }
            break;
        }
      }

      await transaction.complete();
      console.log('Sync transaction completed');
    } catch (error) {
      console.error('Upload error:', error);
      await transaction.rollback();
    }
  }
}

const connector = new SupabaseConnector();

// Todo List Component
function TodoList({ lists, todos, selectedListId, onSelectList, onCreateList, onCreateTodo, onToggleTodo, onDeleteList }) {
  const [newListName, setNewListName] = useState('');
  const [newTodoDescription, setNewTodoDescription] = useState('');

  const handleCreateList = async (e) => {
    e.preventDefault();
    if (newListName.trim()) {
      await onCreateList(newListName.trim());
      setNewListName('');
    }
  };

  const handleCreateTodo = async (e) => {
    e.preventDefault();
    if (newTodoDescription.trim() && selectedListId) {
      await onCreateTodo(selectedListId, newTodoDescription.trim());
      setNewTodoDescription('');
    }
  };

  const selectedList = lists.find(list => list.id === selectedListId);
  const selectedTodos = todos.filter(todo => todo.list_id === selectedListId);

  return (
    <div className="todo-app">
      <div className="header">
        <h1>PowerSync Todo Demo</h1>
        <p className="subtitle">Offline-first synchronization with Supabase</p>
      </div>

      <div className="main-content">
        {/* Lists Section */}
        <div className="lists-section">
          <h2>Lists</h2>
          
          <form onSubmit={handleCreateList} className="create-form">
            <input
              type="text"
              value={newListName}
              onChange={(e) => setNewListName(e.target.value)}
              placeholder="Enter list name"
              className="input-field"
            />
            <button type="submit" className="btn btn-primary">
              Create List
            </button>
          </form>

          <div className="lists-container">
            {lists.map((list) => (
              <div
                key={list.id}
                className={`list-item ${selectedListId === list.id ? 'selected' : ''}`}
                onClick={() => onSelectList(list.id)}
              >
                <span className="list-name">{list.name}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteList(list.id);
                  }}
                  className="btn btn-danger btn-small"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Todos Section */}
        <div className="todos-section">
          {selectedList ? (
            <>
              <h2>Todos for "{selectedList.name}"</h2>
              
              <form onSubmit={handleCreateTodo} className="create-form">
                <input
                  type="text"
                  value={newTodoDescription}
                  onChange={(e) => setNewTodoDescription(e.target.value)}
                  placeholder="Enter todo description"
                  className="input-field"
                />
                <button type="submit" className="btn btn-primary">
                  Add Todo
                </button>
              </form>

              <div className="todos-container">
                {selectedTodos.map((todo) => (
                  <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
                    <input
                      type="checkbox"
                      checked={!!todo.completed}
                      onChange={() => onToggleTodo(todo.id, todo.completed)}
                      className="todo-checkbox"
                    />
                    <span className="todo-description">{todo.description}</span>
                  </div>
                ))}
                {selectedTodos.length === 0 && (
                  <p className="empty-state">No todos yet. Add one above!</p>
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <h2>Select a list</h2>
              <p>Choose a list from the left to view and manage todos</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// PowerSync Provider Component
function PowerSyncProvider({ children }) {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializePowerSync = async () => {
      try {
        console.log('Initializing PowerSync...');
        await powerSync.init();
        console.log('PowerSync initialized');
        
        // Note: We'll skip the actual connection for now since we don't have a PowerSync instance yet
        // await powerSync.connect(connector);
        console.log('PowerSync ready (mock mode)');
        
        setIsReady(true);
      } catch (error) {
        console.error('PowerSync initialization error:', error);
        setError(error.message);
        
        // Still set ready to true for demo purposes
        setIsReady(true);
      }
    };

    initializePowerSync();

    return () => {
      // powerSync.disconnect();
    };
  }, []);

  if (error) {
    return (
      <div className="error-container">
        <h2>PowerSync Error</h2>
        <p>{error}</p>
        <p>Continuing in local-only mode for demo purposes.</p>
      </div>
    );
  }

  if (!isReady) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Initializing PowerSync...</p>
      </div>
    );
  }

  return (
    <PowerSyncContext.Provider value={powerSync}>
      {children}
    </PowerSyncContext.Provider>
  );
}

// Main App Component
function App() {
  const [lists, setLists] = useState([]);
  const [todos, setTodos] = useState([]);
  const [selectedListId, setSelectedListId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('offline');

  // Load data from PowerSync
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load lists
        const listsResult = await powerSync.getAll('SELECT * FROM lists ORDER BY created_at DESC');
        setLists(listsResult);
        
        // Load todos
        const todosResult = await powerSync.getAll('SELECT * FROM todos ORDER BY created_at DESC');
        setTodos(todosResult);
        
        console.log('Loaded data:', { lists: listsResult.length, todos: todosResult.length });
      } catch (error) {
        console.error('Error loading data:', error);
        
        // If no data exists, create some sample data
        if (lists.length === 0) {
          await createSampleData();
        }
      }
    };

    loadData();
  }, []);

  const createSampleData = async () => {
    const listId = uuidv4();
    const now = new Date().toISOString();
    
    // Create sample list
    await powerSync.execute(
      'INSERT INTO lists (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)',
      [listId, 'Sample List', now, now]
    );
    
    // Create sample todos
    const todoIds = [uuidv4(), uuidv4(), uuidv4()];
    const todoDescriptions = [
      'Set up PowerSync integration',
      'Test offline functionality',
      'Build beautiful UI'
    ];
    
    for (let i = 0; i < todoIds.length; i++) {
      await powerSync.execute(
        'INSERT INTO todos (id, list_id, description, completed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
        [todoIds[i], listId, todoDescriptions[i], 0, now, now]
      );
    }
    
    // Reload data
    const listsResult = await powerSync.getAll('SELECT * FROM lists ORDER BY created_at DESC');
    const todosResult = await powerSync.getAll('SELECT * FROM todos ORDER BY created_at DESC');
    setLists(listsResult);
    setTodos(todosResult);
  };

  const handleCreateList = async (name) => {
    const id = uuidv4();
    const now = new Date().toISOString();

    await powerSync.execute(
      'INSERT INTO lists (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)',
      [id, name, now, now]
    );

    // Reload lists
    const listsResult = await powerSync.getAll('SELECT * FROM lists ORDER BY created_at DESC');
    setLists(listsResult);
  };

  const handleCreateTodo = async (listId, description) => {
    const id = uuidv4();
    const now = new Date().toISOString();

    await powerSync.execute(
      'INSERT INTO todos (id, list_id, description, completed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
      [id, listId, description, 0, now, now]
    );

    // Reload todos
    const todosResult = await powerSync.getAll('SELECT * FROM todos ORDER BY created_at DESC');
    setTodos(todosResult);
  };

  const handleToggleTodo = async (todoId, completed) => {
    const now = new Date().toISOString();
    
    await powerSync.execute(
      'UPDATE todos SET completed = ?, updated_at = ? WHERE id = ?',
      [completed ? 0 : 1, now, todoId]
    );

    // Reload todos
    const todosResult = await powerSync.getAll('SELECT * FROM todos ORDER BY created_at DESC');
    setTodos(todosResult);
  };

  const handleDeleteList = async (listId) => {
    await powerSync.execute('DELETE FROM todos WHERE list_id = ?', [listId]);
    await powerSync.execute('DELETE FROM lists WHERE id = ?', [listId]);
    
    if (selectedListId === listId) {
      setSelectedListId(null);
    }

    // Reload data
    const listsResult = await powerSync.getAll('SELECT * FROM lists ORDER BY created_at DESC');
    const todosResult = await powerSync.getAll('SELECT * FROM todos ORDER BY created_at DESC');
    setLists(listsResult);
    setTodos(todosResult);
  };

  return (
    <PowerSyncProvider>
      <div className="App">
        <div className="status-bar">
          <span className={`status-indicator ${connectionStatus}`}></span>
          <span>Status: {connectionStatus === 'offline' ? 'Local Mode (Demo)' : 'Connected'}</span>
        </div>
        
        <TodoList
          lists={lists}
          todos={todos}
          selectedListId={selectedListId}
          onSelectList={setSelectedListId}
          onCreateList={handleCreateList}
          onCreateTodo={handleCreateTodo}
          onToggleTodo={handleToggleTodo}
          onDeleteList={handleDeleteList}
        />
      </div>
    </PowerSyncProvider>
  );
}

export default App;