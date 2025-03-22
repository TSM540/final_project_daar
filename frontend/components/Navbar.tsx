"use client"
import { motion } from 'framer-motion'
import React from 'react'
import ThemeToggle from './ThemeToggle'

function Navbar() {
  return (
    <nav className="flex h-[9vh] border-b-2 items-center justify-between px-6 py-4 z-10 relative">
        <motion.p 
            className="text-2xl font-bold"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
        >
            Daar Moteur de recherche
        </motion.p>
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
        >
            <ThemeToggle className="ml-2" />
        </motion.div>
  </nav>
  )
}

export default Navbar