#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "..");
["data", "data/syllabus", "data/notes", "data/question_papers", "model", "model/embedding", "index", "chat_history"].forEach((d) => {
  const p = path.join(root, d);
  try {
    fs.mkdirSync(p, { recursive: true });
  } catch (_) {}
});
