# 🚀 AI Class Slides Generator

An AI-powered web application that converts **notes or documents into structured PowerPoint presentations (PPT)** using a Large Language Model (LLM).

---

## 🎯 Overview

This project allows users to:
- Paste notes or upload documents (PDF/Text)
- Automatically generate structured slides
- Preview slides with a clean UI
- Download a professional PPT
- Learn interactively with quizzes and slideshow mode

---

## 🧠 Key Idea

Unlike traditional tools, this system acts as an **AI Teaching Assistant** by:
- Structuring content into a logical teaching flow  
- Adapting slide complexity  
- Creating interactive learning experiences  

---

## ✨ Features

### ✅ Core Features
- 📄 Text / PDF input  
- 🤖 AI-powered slide generation (LLM)  
- 🧾 Structured slides (title + bullet points)  
- 📥 Download PPT (.pptx)  
- 👀 Slide preview UI  

---

### 🚀 Advanced Features
- 🧠 **Teaching Flow Intelligence**  
  - Introduction → Concepts → Example → Summary  

- 🎚️ **Slide Density Control**  
  - Concise / Detailed slides  

- 🎓 **Difficulty Mode**  
  - Beginner / Intermediate / Advanced  

- ✍️ **Editable Slides**  
  - Modify content before downloading  

- 🎬 **Slideshow Mode**  
  - Full-screen presentation with navigation  

- 🧩 **Process/Diagram Detection**  
  - Converts steps into structured slides  

- 🧠 **Interactive Quiz**  
  - Attempt questions without seeing answers initially  

- 🔄 **Regenerate Slide**  
  - Regenerate specific slides instead of full deck  

- 📊 **Data Visualization Slides**  
  - Detects numerical data and generates charts  

- 🧹 **Content Cleanup**  
  - Removes noise from messy input notes  

---

## 🛠️ Tech Stack

### Frontend
- React.js  
- Tailwind CSS  
- Framer Motion  
- React Icons  

### Backend
- Python  
- Flask  

### AI
- LLM API (Gemini / OpenAI)  

### Libraries
- python-pptx (PPT generation)  
- PyPDF2 (PDF parsing)  
- Chart.js (data visualization)  

---

## 🧩 Architecture

User Input → Flask Backend → LLM Processing → Slide Structuring → PPT Generation → Frontend Preview → Download  

---

## ⚙️ Installation & Setup

### 1. Clone Repository

git clone https://github.com/your-username/ai-ppt-generator.git  
cd ai-ppt-generator  

---

### 2. Backend Setup

cd backend  
python -m venv venv  
source venv/bin/activate   (Mac/Linux)  
pip install -r requirements.txt  

Run backend:  
python app.py  

---

### 3. Frontend Setup

cd frontend  
npm install  
npm start  

---

## 🔑 Environment Variables

Create a `.env` file in backend:

API_KEY=your_llm_api_key  

---

## 🎮 Usage

1. Enter notes or upload PDF  
2. Select:
   - Number of slides  
   - Difficulty level  
   - Slide density  
3. Click **Generate Slides**  
4. Preview and edit slides  
5. Start slideshow or attempt quiz  
6. Download PPT  

---

## 📸 Screenshots

(Add screenshots of your UI here)

---

## 🚀 Future Improvements

- Voice input → slides  
- Real-time collaboration  
- More themes/templates  
- Cloud storage integration  

---

## 🤝 Contribution

Contributions are welcome! Feel free to fork and improve.

---

## 📜 License

This project is open-source and available under the MIT License.

---

## 👨‍💻 Author

**Rakesh Racharla**

---

## 💬 Final Note

This project demonstrates the integration of **AI + Full Stack Development + UX Design** to solve real-world problems in education and content creation.
