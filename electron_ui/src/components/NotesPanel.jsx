import React, { useState, useEffect } from 'react';
import { Plus, Trash2, FileText } from 'lucide-react';
import { getNotes, createNote, deleteNote } from '../api';

const NotesPanel = () => {
    const [notes, setNotes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newNote, setNewNote] = useState('');
    const [creating, setCreating] = useState(false);

    const fetchNotes = async () => {
        try {
            const data = await getNotes();
            setNotes(data);
        } catch (err) {
            console.error('Failed to fetch notes:', err);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchNotes();
    }, []);

    const handleCreate = async () => {
        if (!newNote.trim()) return;
        setCreating(true);
        try {
            await createNote(newNote);
            setNewNote('');
            fetchNotes();
        } catch (err) {
            console.error('Failed to create note:', err);
        }
        setCreating(false);
    };

    const handleDelete = async (id) => {
        try {
            await deleteNote(id);
            setNotes(notes.filter(n => n.id !== id));
        } catch (err) {
            console.error('Failed to delete note:', err);
        }
    };

    if (loading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-jarvis-cyan animate-pulse font-orbitron">LOADING NOTES...</div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col overflow-hidden animate-in fade-in duration-500">
            <h2 className="text-2xl font-orbitron text-jarvis-cyan mb-4 tracking-wider border-b border-jarvis-cyan/20 pb-2 flex items-center gap-3">
                <FileText size={24} />
                NOTES // <span className="text-sm text-gray-400">{notes.length} ENTRIES</span>
            </h2>

            {/* New Note Input */}
            <div className="mb-4 flex gap-2">
                <input
                    type="text"
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                    placeholder="Add a new note..."
                    className="flex-1 bg-black/40 border border-jarvis-cyan/30 rounded-lg px-4 py-3 text-white placeholder:text-gray-500 font-mono focus:outline-none focus:border-jarvis-cyan/60"
                />
                <button
                    onClick={handleCreate}
                    disabled={creating || !newNote.trim()}
                    className="px-4 py-2 bg-jarvis-cyan/10 border border-jarvis-cyan/30 rounded-lg text-jarvis-cyan hover:bg-jarvis-cyan/20 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                    <Plus size={18} />
                    ADD
                </button>
            </div>

            {/* Notes List */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                {notes.length === 0 ? (
                    <div className="text-gray-500 text-center py-8 font-orbitron">NO NOTES YET</div>
                ) : (
                    notes.map((note) => (
                        <div
                            key={note.id}
                            className="group bg-black/40 border border-jarvis-cyan/20 rounded-lg p-4 hover:border-jarvis-cyan/40 transition-colors"
                        >
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <p className="text-white font-mono whitespace-pre-wrap">{note.content}</p>
                                    <p className="text-xs text-gray-500 mt-2 font-orbitron">{note.created_at}</p>
                                </div>
                                <button
                                    onClick={() => handleDelete(note.id)}
                                    className="p-2 text-gray-500 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default NotesPanel;
