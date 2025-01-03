import React, { useState } from 'react';
import axios from 'axios';
import Select from 'react-select';
import { FaSpinner } from 'react-icons/fa';
import './App.css';
import { TbInfoCircle } from 'react-icons/tb'; // Info ikonu import

const App = () => {
  const [selectedLanguage, setSelectedLanguage] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [fileName, setFileName] = useState('');

  const languageOptions = [
    { value: 'en', label: 'İngilizce' },
    { value: 'tr', label: 'Türkçe' },
    { value: 'es', label: 'İspanyolca' },
    { value: 'de', label: 'Almanca' },
  ];

  const modelOptions = [
    { value: 'tiny', label: 'Tiny Model  ', Tooltip: '75 MB' },
    { value: 'base', label: 'Base Model  ', Tooltip: '150 MB' },
    { value: 'small', label: 'Small Model  ', Tooltip: '300 MB' },
    { value: 'medium', label: 'Medium Model  ', Tooltip: '1.2 GB' },
    { value: 'large', label: 'Large Model  ', Tooltip: '2.9 GB' },
  ];

  // Dosya seçme fonksiyonu
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setAudioFile(file);
    setFileName(file ? file.name : '');
  };

  // Sürükle bırak fonksiyonu
  const handleFileDrop = (e) => {
    e.preventDefault(); // Sayfanın yenilenmesini engelle
    const file = e.dataTransfer.files[0];
    setAudioFile(file);
    setFileName(file ? file.name : '');
  };

  const handleTranscription = async () => {
    if (!audioFile || !selectedLanguage || !selectedModel) {
      alert('Lütfen Dosya, Dil ve Model Seçin');
      return;
    }
  
    setIsLoading(true);
  
    // Transkript bölümünü temizle
    setTranscript('');
  
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('language', selectedLanguage.value);
    formData.append('model', selectedModel.value);
  
    try {
      const response = await axios.post('http://localhost:5000/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
  
      if (response.data.transcript) {
        // Konuşmacı bilgilerini filtrele
        const cleanedTranscript = response.data.transcript.replace(/(speaker\s?\d{1,2}:?\s?)/gi, '');
        
        // Satır sonlarını <br> etiketlerine çevir
        const formattedTranscript = cleanedTranscript.replace(/\n/g, '<br/>');
        setTranscript(formattedTranscript); // HTML formatında transkripti ekle
      } else {
        alert('Transkript elde edilemedi');
      }
    } catch (error) {
      console.error('Transkript Edilirken Hata Oluştu:', error);
      alert('Transkript Edilirken Hata Oluştu');
    } finally {
      setIsLoading(false);
    }
  };

  const customSelectStyles = {
    control: (provided) => ({
      ...provided,
      width: '100%',
      maxWidth: '350px',
      margin: '0 auto',
      borderRadius: '5px',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    }),
    indicatorSeparator: (provided) => ({
      ...provided,
      display: 'none',
    }),
    dropdownIndicator: (provided) => ({
      ...provided,
      color: '#007bff',
    }),
  };

  const customLabel = (label, Tooltip) => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%' }}>
      <span>{label}</span>
      <TbInfoCircle
        className="info-icon"
        title={Tooltip}
        style={{ marginLeft: '5px', cursor: 'pointer' }}
      />
    </div>
  );

  return (
    <div className="App">
      <h1>Whisper Transkript Uygulaması</h1>

      {/* Sürükle bırak alanı */}
      <div
        className="file-upload-container"
        title="Ses Dosyası Seçiniz"
        onDrop={handleFileDrop}
        onDragOver={(e) => e.preventDefault()} // Dragover olayını engelle
        style={{ backgroundColor: 'transparent' }} // Şeffaf arka plan
      >
        <input
          type="file"
          accept="audio/*"
          onChange={handleFileChange}
          id="file-upload"
        />
        <label htmlFor="file-upload" className="file-upload-label">
          <i className="fa fa-upload"></i>
        </label>

        {fileName && <p className="file-name">{fileName}</p>}
      </div>

      <div className="select-container" title="Konuşma Dilini Seçiniz">
        <Select
          options={languageOptions}
          onChange={setSelectedLanguage}
          placeholder="Dil Seçiniz"
          className="select-box"
          styles={customSelectStyles}
        />
      </div>

      <div className="select-container" title="Whisper Modelini Seçiniz">
        <Select
          options={modelOptions.map((option) => ({
            ...option,
            label: customLabel(option.label, option.Tooltip),
          }))}
          onChange={setSelectedModel}
          placeholder="Model Seçiniz"
          className="select-box"
          styles={customSelectStyles}
        />
      </div>

      <button
        onClick={handleTranscription}
        disabled={isLoading}
        className="transcribe-button"
      >
        {isLoading ? (
          <>
            <FaSpinner className="spinner" /> Transkript Ediliyor...
          </>
        ) : (
          'Transkript Et'
        )}
      </button>

      {transcript && (
        <div className="transcript-result">
          <h3>Transcript:</h3>
          <p dangerouslySetInnerHTML={{ __html: transcript }} />
        </div>
      )}
    </div>
  );
};

export default App;
