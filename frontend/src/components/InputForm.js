import React, { useState } from "react";
import { motion } from "framer-motion";
import { FiFileText, FiUploadCloud, FiZap } from "react-icons/fi";

function InputForm({ loading, onSubmit }) {
  const [notes, setNotes] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await onSubmit({ notes, file: selectedFile });
  };

  const handleFileSelection = (file) => {
    if (!file) {
      return;
    }

    setSelectedFile(file);
  };

  return (
    <motion.section
      className="panel"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <div className="panel-header">
        <div>
          <p className="eyebrow">Source Material</p>
          <h2>Turn rough notes into a clean lesson deck</h2>
          <p className="panel-copy">
            Paste lecture notes, training outlines, or upload a PDF/TXT file. The existing backend flow
            stays unchanged.
          </p>
        </div>

        <div className="hero-chip-group">
          <span className="badge">
            <FiZap />
            AI structured
          </span>
          <span className="badge subtle">
            <FiFileText />
            PDF / TXT
          </span>
        </div>
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <div className="setting-group">
          <label className="setting-label" htmlFor="notes-textarea">
            Paste notes
          </label>
          <textarea
            id="notes-textarea"
            className="notes-textarea"
            placeholder="Paste topics, learning objectives, explanations, examples, or a process you want converted into slides..."
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </div>

        <div className="input-footer">
          <div
            className={`upload-zone ${dragActive ? "dragging" : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragActive(false);
              handleFileSelection(event.dataTransfer.files?.[0]);
            }}
          >
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={(event) => handleFileSelection(event.target.files?.[0])}
            />

            <span className="upload-icon">
              <FiUploadCloud />
            </span>

            <div>
              <strong>Drop a PDF or TXT file here</strong>
              <p>or click to browse. The uploaded file can be used instead of pasted notes.</p>
            </div>

            {selectedFile ? <span className="file-pill">{selectedFile.name}</span> : null}
          </div>

          <div className="submit-stack">
            <p className="muted-copy">
              Tip: longer notes usually produce a more coherent deck and better quiz questions.
            </p>

            <button
              type="submit"
              className="primary-button"
              disabled={loading || (!notes.trim() && !selectedFile)}
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  Generating slides...
                </>
              ) : (
                <>
                  <FiZap />
                  Generate class slides
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </motion.section>
  );
}

export default InputForm;
