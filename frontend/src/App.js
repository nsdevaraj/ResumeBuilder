import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LinkedInButton = ({ onClick, loading }) => (
  <button
    onClick={onClick}
    disabled={loading}
    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 flex items-center space-x-2 shadow-lg"
  >
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M16.338 16.338H13.67V12.16c0-.995-.017-2.277-1.387-2.277-1.39 0-1.601 1.086-1.601 2.207v4.248H8.014v-8.59h2.559v1.174h.037c.356-.675 1.227-1.387 2.526-1.387 2.703 0 3.203 1.778 3.203 4.092v4.711zM5.005 6.575a1.548 1.548 0 11-.003-3.096 1.548 1.548 0 01.003 3.096zm-1.337 9.763H6.34v-8.59H3.667v8.59zM17.668 1H2.328C1.595 1 1 1.581 1 2.298v15.403C1 18.418 1.595 19 2.328 19h15.34c.734 0 1.332-.582 1.332-1.299V2.298C19 1.581 18.402 1 17.668 1z" clipRule="evenodd"/>
    </svg>
    <span>{loading ? "Connecting..." : "Connect with LinkedIn"}</span>
  </button>
);

const TemplateCard = ({ template, selected, onClick }) => (
  <div 
    className={`cursor-pointer border-2 rounded-lg p-4 transition duration-300 ${
      selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
    }`}
    onClick={onClick}
  >
    <img 
      src={template.preview_image} 
      alt={template.name}
      className="w-full h-48 object-cover rounded-lg mb-4"
    />
    <h3 className="font-bold text-lg mb-2">{template.name}</h3>
    <p className="text-gray-600 text-sm">{template.description}</p>
  </div>
);

const ProfilePreview = ({ profile }) => (
  <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
    <h2 className="text-2xl font-bold mb-4 text-gray-800">Profile Preview</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <p className="text-lg"><span className="font-semibold">Name:</span> {profile.first_name} {profile.last_name}</p>
        <p className="text-lg"><span className="font-semibold">Headline:</span> {profile.headline || "Not available"}</p>
        <p className="text-lg"><span className="font-semibold">Email:</span> {profile.email || "Not available"}</p>
      </div>
    </div>
  </div>
);

const ResumePreview = ({ resumeData, template }) => (
  <div className="bg-white rounded-lg shadow-lg p-8 max-w-4xl mx-auto">
    <div className={`resume-template ${template.style}`}>
      {/* Header */}
      <div className="text-center mb-8 border-b-2 border-gray-200 pb-6">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          {resumeData.profile.first_name} {resumeData.profile.last_name}
        </h1>
        {resumeData.profile.headline && (
          <h2 className="text-xl text-gray-600 mb-2">{resumeData.profile.headline}</h2>
        )}
        {resumeData.profile.email && (
          <p className="text-gray-600">{resumeData.profile.email}</p>
        )}
      </div>

      {/* Professional Summary */}
      {resumeData.profile.headline && (
        <div className="mb-8">
          <h3 className="text-2xl font-bold text-gray-800 mb-4 border-l-4 border-blue-500 pl-4">
            Professional Summary
          </h3>
          <p className="text-gray-700 leading-relaxed">{resumeData.profile.headline}</p>
        </div>
      )}

      {/* Experience Section Placeholder */}
      <div className="mb-8">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 border-l-4 border-blue-500 pl-4">
          Professional Experience
        </h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-600 italic">
            Experience details will be populated from your LinkedIn profile. 
            Note: Some LinkedIn API endpoints require additional permissions for detailed work experience.
          </p>
        </div>
      </div>

      {/* Education Section Placeholder */}
      <div className="mb-8">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 border-l-4 border-blue-500 pl-4">
          Education
        </h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-600 italic">
            Education details will be populated from your LinkedIn profile.
          </p>
        </div>
      </div>

      {/* Skills Section Placeholder */}
      <div className="mb-8">
        <h3 className="text-2xl font-bold text-gray-800 mb-4 border-l-4 border-blue-500 pl-4">
          Skills
        </h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-600 italic">
            Skills will be populated from your LinkedIn profile.
          </p>
        </div>
      </div>
    </div>
  </div>
);

function App() {
  const [currentStep, setCurrentStep] = useState('connect'); // connect, templates, preview
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [generatedResume, setGeneratedResume] = useState(null);
  const [error, setError] = useState('');

  // Check URL parameters for LinkedIn callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const userId = urlParams.get('user_id');
    const errorParam = urlParams.get('error');

    if (success && userId) {
      fetchProfile(userId);
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (errorParam) {
      setError('Failed to connect with LinkedIn. Please try again.');
      setCurrentStep('connect');
    }
  }, []);

  // Fetch templates on component mount
  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchProfile = async (userId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/profile/${userId}`);
      setProfile(response.data);
      setCurrentStep('templates');
    } catch (error) {
      console.error('Error fetching profile:', error);
      setError('Failed to fetch profile data');
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setError('Failed to fetch templates');
    }
  };

  const handleLinkedInConnect = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/auth/linkedin`);
      window.location.href = response.data.auth_url;
    } catch (error) {
      console.error('Error initiating LinkedIn connection:', error);
      setError('Failed to connect with LinkedIn');
      setLoading(false);
    }
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
  };

  const handleGenerateResume = async () => {
    if (!selectedTemplate || !profile) return;

    try {
      setLoading(true);
      const response = await axios.post(`${API}/generate-resume?user_id=${profile.user_id}&template_id=${selectedTemplate.id}`);
      setGeneratedResume(response.data.data);
      setCurrentStep('preview');
    } catch (error) {
      console.error('Error generating resume:', error);
      setError('Failed to generate resume');
    } finally {
      setLoading(false);
    }
  };

  const resetApp = () => {
    setCurrentStep('connect');
    setProfile(null);
    setSelectedTemplate(null);
    setGeneratedResume(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-3xl font-bold text-gray-900">LinkedIn Resume Builder</h1>
            {currentStep !== 'connect' && (
              <button
                onClick={resetApp}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Start Over
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Step 1: LinkedIn Connection */}
        {currentStep === 'connect' && (
          <div className="text-center py-12">
            <div className="max-w-2xl mx-auto">
              <h2 className="text-4xl font-bold text-gray-900 mb-8">
                Create Your Professional Resume
              </h2>
              <p className="text-xl text-gray-600 mb-12">
                Connect with LinkedIn to automatically import your profile data and generate a beautiful resume in minutes.
              </p>
              <LinkedInButton onClick={handleLinkedInConnect} loading={loading} />
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="font-bold text-lg mb-2">1. Connect</h3>
                  <p className="text-gray-600">Authorize with your LinkedIn account</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="font-bold text-lg mb-2">2. Choose Template</h3>
                  <p className="text-gray-600">Select from professional resume designs</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                  <h3 className="font-bold text-lg mb-2">3. Generate</h3>
                  <p className="text-gray-600">Get your polished resume instantly</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Template Selection */}
        {currentStep === 'templates' && profile && (
          <div>
            <ProfilePreview profile={profile} />
            
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold mb-6 text-gray-800">Choose Your Resume Template</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {templates.map((template) => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    selected={selectedTemplate?.id === template.id}
                    onClick={() => handleTemplateSelect(template)}
                  />
                ))}
              </div>
              
              {selectedTemplate && (
                <div className="text-center">
                  <button
                    onClick={handleGenerateResume}
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg transition duration-300"
                  >
                    {loading ? "Generating Resume..." : "Generate My Resume"}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Resume Preview */}
        {currentStep === 'preview' && generatedResume && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Your Resume is Ready!</h2>
              <p className="text-gray-600 mb-6">Here's your professional resume generated from your LinkedIn profile.</p>
              <div className="space-x-4">
                <button
                  onClick={() => setCurrentStep('templates')}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300"
                >
                  Try Different Template
                </button>
                <button
                  onClick={() => window.print()}
                  className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-6 rounded-lg transition duration-300"
                >
                  Print Resume
                </button>
              </div>
            </div>
            
            <ResumePreview 
              resumeData={generatedResume} 
              template={selectedTemplate}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
