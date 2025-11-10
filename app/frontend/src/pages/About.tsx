import React from 'react'

const About: React.FC = () => {
  return (
    <main className="min-h-screen bg-white text-gray-800 px-8 py-16">
      <section className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">About NeuroLearn</h1>

        <p className="text-lg mb-4 leading-relaxed">
          NeuroLearn is an adaptive, focus-aware learning platform designed to
          enhance study efficiency through real-time brainwave feedback.
        </p>

        <p className="text-lg mb-4 leading-relaxed">
          By integrating EEG-based attention tracking with personalized content
          delivery, NeuroLearn helps students maintain optimal engagement and
          improve knowledge retention.
        </p>

        <p className="text-lg leading-relaxed">
          Our mission is to bridge neuroscience and education — creating smarter,
          more responsive learning environments that evolve with each learner.
        </p>
      </section>
    </main>
  )
}

export default About