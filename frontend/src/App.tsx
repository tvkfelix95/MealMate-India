import { useState } from 'react'
import CustomerAuth from './CustomerAuth'
import type { CustomerAuthMode } from './CustomerAuth'

type Answers = {
  preference: string
  allergies: string
  budget: string
  skill: string
  time: string
  equipment: string[]
  cuisine: string
}

const initialAnswers: Answers = {
  preference: '',
  allergies: '',
  budget: '',
  skill: '',
  time: '',
  equipment: [],
  cuisine: '',
}

const steps = [
  { title: 'Your food preference', description: 'What kind of meals should we plan for you?', key: 'preference' },
  { title: 'Anything to avoid?', description: 'Tell us about allergies or ingredients you dislike.', key: 'allergies' },
  { title: 'Your everyday rhythm', description: 'Set a budget and choose your cooking comfort level.', key: 'budget' },
  { title: 'Your kitchen setup', description: 'Help us suggest meals that fit your time and equipment.', key: 'time' },
  { title: 'Your favourite flavours', description: 'Choose a cuisine to get your first meal plan started.', key: 'cuisine' },
]

const meals = [
  { slot: 'Breakfast', dish: 'Your breakfast pick', time: 'Personalised', icon: '🍚' },
  { slot: 'Lunch', dish: 'Your lunch pick', time: 'Personalised', icon: '🍋' },
  { slot: 'Dinner', dish: 'Your dinner pick', time: 'Personalised', icon: '🥣' },
]

const preferenceOptions = ['Vegetarian', 'Egg', 'Non-vegetarian']
const skillOptions = ['Beginner', 'Intermediate', 'Experienced']
const timeOptions = ['Under 20 minutes', '20–40 minutes', 'More than 40 minutes']
const equipmentOptions = ['Stovetop', 'Pressure cooker', 'Mixer / blender', 'Oven or air fryer']
const cuisineOptions = ['South Indian', 'North Indian', 'East Indian', 'West Indian']

function ChoiceCard({ label, selected, onClick }: { label: string; selected: boolean; onClick: () => void }) {
  return <button type="button" aria-pressed={selected} onClick={onClick} className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3.5 text-left font-semibold transition ${selected ? 'border-[#e47742] bg-[#fff3df] text-[#b85b2b] shadow-sm' : 'border-[#e5ebe1] bg-white text-[#48634e] hover:border-[#b7cbb1]'}`}><span>{label}</span><span className={`grid h-5 w-5 place-items-center rounded-full border text-xs ${selected ? 'border-[#e47742] bg-[#e47742] text-white' : 'border-[#cbd8c8] text-transparent'}`}>✓</span></button>
}

function App() {
  const [isOnboarding, setIsOnboarding] = useState(false)
  const [customerAuthMode, setCustomerAuthMode] = useState<CustomerAuthMode | null>(null)
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Answers>(initialAnswers)
  const currentStep = steps[step]

  const updateAnswer = <K extends keyof Answers>(key: K, value: Answers[K]) => setAnswers((current) => ({ ...current, [key]: value }))
  const isStepValid = () => {
    if (step === 1) return true
    if (step === 2) return Boolean(answers.budget) && Boolean(answers.skill)
    if (step === 3) return Boolean(answers.time) && answers.equipment.length > 0
    return Boolean(answers[currentStep.key as keyof Answers])
  }

  const startOnboarding = () => {
    setAnswers(initialAnswers)
    setStep(0)
    setIsOnboarding(true)
  }

  const nextStep = () => {
    if (!isStepValid()) return
    if (step < steps.length - 1) setStep((current) => current + 1)
    else setIsOnboarding(false)
  }

  const toggleEquipment = (equipment: string) => updateAnswer('equipment', answers.equipment.includes(equipment) ? answers.equipment.filter((item) => item !== equipment) : [...answers.equipment, equipment])

  if (isOnboarding) {
    return <Onboarding step={step} answers={answers} currentStep={currentStep} isStepValid={isStepValid()} onBack={() => step === 0 ? setIsOnboarding(false) : setStep((current) => current - 1)} onContinue={nextStep} updateAnswer={updateAnswer} toggleEquipment={toggleEquipment} />
  }

  if (customerAuthMode) {
    return <CustomerAuth initialMode={customerAuthMode} onBack={() => setCustomerAuthMode(null)} />
  }

  return <Landing onStart={startOnboarding} onAuth={setCustomerAuthMode} />
}

function Landing({ onStart, onAuth }: { onStart: () => void; onAuth: (mode: CustomerAuthMode) => void }) {
  return <main className="min-h-screen overflow-hidden bg-[#fffaf2] text-[#24352a]">
    <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5 sm:px-8"><a className="flex items-center gap-2 text-lg font-bold tracking-tight" href="#top"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f28c5b] text-lg shadow-sm">✦</span>MealMate <span className="text-[#e47742]">India</span></a><div className="flex items-center gap-2"><button onClick={() => onAuth('login')} className="rounded-full border border-[#d8e3d4] px-3 py-2 text-xs font-semibold text-[#48634e] transition hover:border-[#9fb899] hover:bg-white sm:px-4 sm:text-sm">Log in</button><button onClick={() => onAuth('register')} className="rounded-full bg-[#e47742] px-3 py-2 text-xs font-bold text-white transition hover:bg-[#d96632] sm:px-4 sm:text-sm">Create account</button><a className="hidden rounded-full border border-[#d8e3d4] px-4 py-2 text-sm font-semibold text-[#48634e] transition hover:border-[#9fb899] hover:bg-white sm:inline-flex" href="#how-it-works">How it works</a></div></nav>
    <section id="top" className="mx-auto grid max-w-6xl items-center gap-12 px-5 pb-16 pt-10 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:pb-24 lg:pt-16"><div><p className="mb-5 inline-flex items-center gap-2 rounded-full bg-[#e8f0e4] px-4 py-2 text-sm font-semibold text-[#537055]">🌿 Made for everyday Indian kitchens</p><h1 className="max-w-2xl text-5xl font-black leading-[1.05] tracking-[-0.04em] text-[#24352a] sm:text-6xl">Cook something <span className="text-[#e47742]">good</span> today.</h1><p className="mt-6 max-w-xl text-lg leading-8 text-[#637466]">MealMate helps you plan simple, delicious South Indian meals that fit your time, budget and the ingredients you already love.</p><div className="mt-8 flex flex-col gap-3 sm:flex-row"><button onClick={onStart} className="rounded-full bg-[#e47742] px-6 py-3.5 font-bold text-white shadow-[0_8px_20px_rgba(228,119,66,0.24)] transition hover:-translate-y-0.5 hover:bg-[#d96632]">Plan my meals <span className="ml-2">→</span></button><button className="rounded-full border border-[#d8e3d4] bg-white px-6 py-3.5 font-bold text-[#48634e] transition hover:border-[#9fb899]">Explore recipes</button></div><div className="mt-8 flex items-center gap-3 text-sm text-[#718072]"><div className="flex -space-x-2"><span className="grid h-8 w-8 place-items-center rounded-full border-2 border-[#fffaf2] bg-[#f3b18e]">👩🏽</span><span className="grid h-8 w-8 place-items-center rounded-full border-2 border-[#fffaf2] bg-[#c5d6b7]">👨🏾</span><span className="grid h-8 w-8 place-items-center rounded-full border-2 border-[#fffaf2] bg-[#f0d39d]">👩🏾</span></div><span>Thoughtful meals for real Indian routines</span></div></div><div className="relative mx-auto w-full max-w-md lg:justify-self-end"><div className="absolute -right-5 -top-5 h-32 w-32 rounded-full bg-[#f5d99a] blur-2xl" /><div className="absolute -bottom-8 -left-5 h-40 w-40 rounded-full bg-[#cfe2c7] blur-2xl" /><div className="relative rounded-[2rem] bg-[#f2d19c] p-3 shadow-[0_24px_60px_rgba(118,91,53,0.16)]"><div className="rounded-[1.5rem] bg-[#fffdf8] p-5 sm:p-7"><div className="flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-[#99a796]">A plan made for you</p><h2 className="mt-1 text-2xl font-black">Your meal plan</h2></div><span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#e8f0e4] text-xl">☀️</span></div><div className="mt-6 space-y-3">{meals.map((meal) => <div key={meal.slot} className="flex items-center gap-3 rounded-2xl border border-[#edf0e8] bg-[#fff] p-3"><span className="grid h-12 w-12 place-items-center rounded-xl bg-[#fff3df] text-2xl">{meal.icon}</span><div className="min-w-0 flex-1"><p className="text-xs font-semibold text-[#9aa69b]">{meal.slot}</p><p className="truncate font-bold text-[#354b3a]">{meal.dish}</p></div><span className="text-xs font-semibold text-[#99a796]">{meal.time}</span></div>)}</div><div className="mt-5 flex items-center justify-between rounded-2xl bg-[#f5f8f1] px-4 py-3 text-sm"><span className="font-semibold text-[#637466]">Your preferences</span><span className="font-black text-[#537055]">Ready to personalise</span></div></div></div></div></section>
    <section id="how-it-works" className="border-y border-[#edf0e8] bg-white/60 px-5 py-14 sm:px-8"><div className="mx-auto max-w-6xl"><div className="max-w-xl"><p className="text-sm font-bold uppercase tracking-[0.18em] text-[#e47742]">A little help, every day</p><h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Less wondering. More cooking.</h2></div><div className="mt-10 grid gap-4 md:grid-cols-3"><div className="rounded-3xl bg-[#f5f8f1] p-6"><span className="text-3xl">🧺</span><h3 className="mt-5 text-xl font-black">Tell us your routine</h3><p className="mt-2 leading-7 text-[#718072]">Set your budget, cooking time, skill level and preferences.</p></div><div className="rounded-3xl bg-[#fff3df] p-6"><span className="text-3xl">🍛</span><h3 className="mt-5 text-xl font-black">Get a plan that fits</h3><p className="mt-2 leading-7 text-[#718072]">Receive easy meal ideas for every part of your day.</p></div><div className="rounded-3xl bg-[#f8e9e2] p-6"><span className="text-3xl">🛒</span><h3 className="mt-5 text-xl font-black">Shop with confidence</h3><p className="mt-2 leading-7 text-[#718072]">Follow clear recipes and take a ready-to-go grocery list.</p></div></div></div></section><footer className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-8 text-sm text-[#8a988b] sm:flex-row sm:items-center sm:justify-between sm:px-8"><span className="font-bold text-[#637466]">MealMate India</span><span>Good food, made a little easier.</span></footer>
  </main>
}

function Onboarding({ step, answers, currentStep, isStepValid, onBack, onContinue, updateAnswer, toggleEquipment }: { step: number; answers: Answers; currentStep: (typeof steps)[number]; isStepValid: boolean; onBack: () => void; onContinue: () => void; updateAnswer: <K extends keyof Answers>(key: K, value: Answers[K]) => void; toggleEquipment: (equipment: string) => void }) {
  return <main className="min-h-screen bg-[#fffaf2] px-5 py-5 text-[#24352a] sm:px-8 sm:py-8"><div className="mx-auto max-w-3xl"><header className="flex items-center justify-between"><a className="flex items-center gap-2 text-lg font-bold tracking-tight" href="#top"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[#f28c5b] text-lg shadow-sm">✦</span>MealMate <span className="text-[#e47742]">India</span></a><button onClick={onBack} className="text-sm font-semibold text-[#718072] hover:text-[#e47742]">Save for later</button></header><div className="mt-10"><div className="flex items-center justify-between text-sm font-bold text-[#718072]"><span>Step {step + 1} of {steps.length}</span><span>{Math.round(((step + 1) / steps.length) * 100)}%</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-[#e5ebe1]"><div className="h-full rounded-full bg-[#e47742] transition-all duration-300" style={{ width: `${((step + 1) / steps.length) * 100}%` }} /></div></div><section className="mt-10 rounded-[2rem] border border-[#edf0e8] bg-white p-6 shadow-[0_20px_50px_rgba(118,91,53,0.08)] sm:p-10"><p className="text-sm font-bold uppercase tracking-[0.18em] text-[#e47742]">Let’s make it personal</p><h1 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">{currentStep.title}</h1><p className="mt-3 text-[#718072]">{currentStep.description}</p><div className="mt-8">{step === 0 && <div className="grid gap-3 sm:grid-cols-3">{preferenceOptions.map((option) => <ChoiceCard key={option} label={option} selected={answers.preference === option} onClick={() => updateAnswer('preference', option)} />)}</div>}{step === 1 && <div><label className="text-sm font-bold text-[#48634e]" htmlFor="allergies">Allergies and disliked ingredients <span className="font-normal text-[#99a796]">(optional)</span></label><textarea id="allergies" value={answers.allergies} onChange={(event) => updateAnswer('allergies', event.target.value)} placeholder="For example: peanuts, brinjal, very spicy food" className="mt-3 min-h-36 w-full resize-y rounded-2xl border border-[#dfe8dc] bg-[#fffdf8] p-4 text-[#354b3a] outline-none transition placeholder:text-[#aab5aa] focus:border-[#e47742] focus:ring-4 focus:ring-[#f9dfcc]" /><p className="mt-2 text-xs text-[#99a796]">We’ll use this to keep future suggestions safer and more comfortable.</p></div>}{step === 2 && <div className="grid gap-7 sm:grid-cols-2"><div><label className="text-sm font-bold text-[#48634e]" htmlFor="budget">Daily food budget</label><div className="mt-3 flex items-center rounded-2xl border border-[#dfe8dc] bg-[#fffdf8] px-4 focus-within:border-[#e47742] focus-within:ring-4 focus-within:ring-[#f9dfcc]"><span className="text-lg font-bold text-[#99a796]">₹</span><input id="budget" type="number" min="0" value={answers.budget} onChange={(event) => updateAnswer('budget', event.target.value)} placeholder="Amount in rupees" className="w-full bg-transparent p-4 pl-2 outline-none placeholder:text-[#aab5aa]" /></div></div><div><p className="text-sm font-bold text-[#48634e]">Cooking skill</p><div className="mt-3 grid gap-2">{skillOptions.map((option) => <ChoiceCard key={option} label={option} selected={answers.skill === option} onClick={() => updateAnswer('skill', option)} />)}</div></div></div>}{step === 3 && <div className="grid gap-8 sm:grid-cols-2"><div><p className="text-sm font-bold text-[#48634e]">Available cooking time</p><div className="mt-3 grid gap-2">{timeOptions.map((option) => <ChoiceCard key={option} label={option} selected={answers.time === option} onClick={() => updateAnswer('time', option)} />)}</div></div><div><p className="text-sm font-bold text-[#48634e]">Kitchen equipment <span className="font-normal text-[#99a796]">(choose all that apply)</span></p><div className="mt-3 grid gap-2">{equipmentOptions.map((option) => <ChoiceCard key={option} label={option} selected={answers.equipment.includes(option)} onClick={() => toggleEquipment(option)} />)}</div></div></div>}{step === 4 && <div className="grid gap-3 sm:grid-cols-2">{cuisineOptions.map((option) => <ChoiceCard key={option} label={option} selected={answers.cuisine === option} onClick={() => updateAnswer('cuisine', option)} />)}</div>}</div>{!isStepValid && <p className="mt-5 text-sm font-semibold text-[#c45f42]">Please complete the required selection before continuing.</p>}<div className="mt-10 flex flex-col-reverse gap-3 sm:flex-row sm:justify-between"><button onClick={onBack} className="rounded-full border border-[#d8e3d4] px-6 py-3.5 font-bold text-[#48634e] transition hover:border-[#9fb899]">{step === 0 ? 'Back to home' : '← Back'}</button><button onClick={onContinue} className="rounded-full bg-[#e47742] px-7 py-3.5 font-bold text-white shadow-[0_8px_20px_rgba(228,119,66,0.2)] transition hover:bg-[#d96632]">{step === steps.length - 1 ? 'Create my plan' : 'Continue →'}</button></div></section></div></main>
}

export default App
