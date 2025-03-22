"use client"
import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { Book, Search, BookOpen, Library, ExternalLink } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

export default function HomePage() {
  const router = useRouter()
  const [isNavigating, setIsNavigating] = useState(false)
  const [currentPage, setCurrentPage] = useState(0)
  const totalPages = 3

  const handleStartSearch = () => {
    setIsNavigating(true)
    
    // Sequence through the pages
    const pageInterval = setInterval(() => {
      setCurrentPage(prev => {
        if (prev >= totalPages - 1) {
          clearInterval(pageInterval)
          return prev
        }
        return prev + 1
      })
    }, 800)
    
    // Delay the navigation to allow the animation to complete
    setTimeout(() => {
      router.push("/form")
    }, 3500)
  }

  return (
    <div className="min-h-screen flex flex-col overflow-hidden">
      <AnimatePresence>
        {!isNavigating ? (
          <motion.main 
            key="main"
            className="flex-1 container mx-auto px-4 py-12 flex flex-col items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ 
              opacity: 0,
              transition: { duration: 0.5 }
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <Card className="w-full max-w-4xl bg-card/50 backdrop-blur-sm">
                <CardContent className="p-8">
                  <motion.div 
                    className="flex justify-center mb-8"
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.3, duration: 0.5 }}
                  >
                    <div className="relative">
                      <motion.div
                        animate={{ 
                          rotateY: [0, 10, 0, -10, 0],
                        }}
                        transition={{ 
                          repeat: Infinity, 
                          duration: 5,
                          ease: "easeInOut" 
                        }}
                      >
                        <Book className="text-primary w-24 h-24" />
                      </motion.div>
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.8, type: "spring" }}
                      >
                        <Search className="text-foreground absolute bottom-0 right-0 w-10 h-10" />
                      </motion.div>
                    </div>
                  </motion.div>

                  <motion.h1 
                    className="text-4xl font-bold text-center mb-4"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                  >
                    Discover Your Next Great Read
                  </motion.h1>
                  
                  <motion.p 
                    className="text-center text-muted-foreground mb-8 max-w-2xl mx-auto"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.6 }}
                  >
                    Search through thousands of books by title, author, or keyword. 
                    Our advanced search engine helps you find exactly what you re looking for.
                  </motion.p>

                  <motion.div 
                    className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 }}
                  >
                    <FeatureCard 
                      icon={<Search className="w-8 h-8 text-primary" />}
                      title="Multiple Search Options"
                      description="Simple, advanced, and TF-IDF cosine similarity search capabilities"
                      delay={0.8}
                    />
                    <FeatureCard 
                      icon={<BookOpen className="w-8 h-8 text-primary" />}
                      title="Detailed Book Information"
                      description="View covers, authors, subjects, languages, and download counts"
                      delay={1.0}
                    />
                    <FeatureCard 
                      icon={<Library className="w-8 h-8 text-primary" />}
                      title="Personalized Recommendations"
                      description="Get suggestions for other books you might enjoy"
                      delay={1.2}
                    />
                  </motion.div>

                  <motion.div 
                    className="flex justify-center"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.3 }}
                    whileHover={{ scale: 1.05 }}
                  >
                    <Button 
                      size="lg" 
                      className="text-lg px-8 py-6"
                      onClick={handleStartSearch}
                    >
                      Start Your Search
                      <motion.div
                        animate={{ x: [0, 5, 0] }}
                        transition={{ repeat: Infinity, duration: 1.5 }}
                      >
                        <Search className="ml-2 h-5 w-5" />
                      </motion.div>
                    </Button>
                  </motion.div>
                </CardContent>
              </Card>
            </motion.div>
          </motion.main>
        ) : (
          <motion.div 
            key="book-animation"
            className="fixed inset-0 flex items-center justify-center z-50 bg-background/80"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="relative w-80 h-96 perspective-1200">
              {/* Book cover and spine */}
              <div className="absolute inset-0 bg-primary/20 rounded-lg shadow-xl overflow-hidden flex">
                <div className="w-6 h-full bg-primary/30 shadow-inner"></div>
                <div className="flex-1"></div>
              </div>
              
              {/* Fixed left page */}
              <div className="absolute top-0 left-6 bottom-0 w-[calc(50%-6px)] bg-background border-r border-primary/30 flex items-center justify-center p-4">
                <div className="text-center">
                  <Book className="mx-auto text-primary/60 w-12 h-12 mb-3" />
                  <p className="text-primary text-sm">Your reading journey begins here</p>
                </div>
              </div>

              {/* Multiple turning pages */}
              {[...Array(totalPages)].map((_, i) => (
                <AnimatePresence key={`page-${i}`}>
                  {currentPage <= i && (
                    <motion.div
                      className="absolute top-0 right-0 w-[calc(50%-3px)] h-full origin-left bg-background shadow-md"
                      initial={{ rotateY: 0 }}
                      animate={{ 
                        rotateY: currentPage === i ? -180 : 0,
                        transition: { 
                          duration: 1,
                          ease: [0.645, 0.045, 0.355, 1.000], 
                          delay: 0.1
                        }
                      }}
                      exit={{ rotateY: -180 }}
                      style={{ 
                        transformStyle: "preserve-3d",
                        zIndex: totalPages - i
                      }}
                    >
                      {/* Front of page */}
                      <div 
                        className="absolute inset-0 p-4 flex flex-col items-center justify-center border border-primary/10"
                        style={{ backfaceVisibility: "hidden" }}
                      >
                        <p className="text-primary font-medium text-center">
                          {i === 0 ? "Searching for books..." : 
                           i === 1 ? "Finding your next read..." : 
                                    "Almost there..."}
                        </p>
                        {i === 0 && <Search className="mt-4 text-primary/70 w-8 h-8" />}
                        {i === 1 && <BookOpen className="mt-4 text-primary/70 w-8 h-8" />}
                        {i === 2 && <Library className="mt-4 text-primary/70 w-8 h-8" />}
                      </div>
                      
                      {/* Back of page */}
                      <div 
                        className="absolute inset-0 bg-background/90 p-4 flex items-center justify-center border border-primary/10"
                        style={{ 
                          backfaceVisibility: "hidden",
                          transform: "rotateY(180deg)",
                        }}
                      >
                        {i < totalPages - 1 ? (
                          <p className="text-primary text-sm text-center">Turn the page to continue...</p>
                        ) : null}
                      </div>
                      
                      {/* Page turning shadow effect */}
                      <motion.div
                        className="absolute top-0 w-full h-full bg-black/10 origin-left"
                        initial={{ opacity: 0 }}
                        animate={{ 
                          opacity: currentPage === i ? [0, 0.3, 0] : 0,
                          rotateY: currentPage === i ? -180 : 0,
                          transition: { 
                            duration: 1,
                            ease: [0.645, 0.045, 0.355, 1.000]
                          }
                        }}
                        style={{ transformStyle: "preserve-3d" }}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              ))}
              
              {/* Right side content (visible after all pages are turned) */}
              <motion.div 
                className="absolute top-0 right-0 w-[calc(50%-3px)] h-full bg-background p-6 flex flex-col items-center justify-center"
                initial={{ opacity: 0 }}
                animate={{ 
                  opacity: currentPage >= totalPages - 1 ? 1 : 0,
                  transition: { delay: 0.8, duration: 0.5 }
                }}
              >
                <motion.div
                  className="text-center"
                  initial={{ scale: 0.9 }}
                  animate={{ 
                    scale: currentPage >= totalPages - 1 ? [0.9, 1.1, 1] : 0.9,
                    transition: { delay: 1, duration: 0.5 }
                  }}
                >
                  <ExternalLink className="mx-auto text-primary w-12 h-12 mb-4" />
                  <h3 className="font-bold text-lg text-primary mb-2">Redirecting to Search</h3>
                  <p className="text-primary/70 text-sm mb-4">Taking you to your favorite book search engine</p>
                  <motion.div
                    className="w-12 h-1 mx-auto bg-primary/40 rounded-full overflow-hidden"
                    initial={{ width: "0%" }}
                    animate={{ 
                      width: currentPage >= totalPages - 1 ? "100%" : "0%",
                      transition: { delay: 1.2, duration: 1.5 }
                    }}
                  />
                </motion.div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.footer 
        className="py-6 border-t"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
      >
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>© 2025 Daar Moteur de recherche. All rights reserved.</p>
        </div>
      </motion.footer>
    </div>
  )
}

interface FeatureCardProps {
  icon: React.ReactNode
  title: string
  description: string
  delay: number
}

function FeatureCard({ icon, title, description, delay }: FeatureCardProps) {
  return (
    <motion.div 
      className="flex flex-col items-center text-center p-4 bg-muted/50 rounded-lg"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        delay,
        duration: 0.5
      }}
      whileHover={{ 
        scale: [1, 1.06],
        boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
        transition: {
          scale: {
            type: "spring",
            stiffness: 300,
            damping: 10
          },
          duration: 0.3
        }
      }}
      whileTap={{ scale: 0.98 }}
    >
      <motion.div 
        className="mb-4"
        whileHover={{ 
          rotate: [0, -10, 10, -10, 0],
          transition: { duration: 0.5 }
        }}
      >
        {icon}
      </motion.div>
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </motion.div>
  )
}