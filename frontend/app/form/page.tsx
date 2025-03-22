/* eslint-disable @typescript-eslint/no-explicit-any */
"use client"
// import ThemeToggle from "../components/ThemeToggle";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Loader from "@/components/Loader";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { Home } from "lucide-react";
// import { DialogTitle } from "@radix-ui/react-dialog";
// import Image from "next/image";

const urlBaseRequete = "http://localhost:8000/server/books/?";
const cosineUrlBase = "http://localhost:8000/data/books/keywords/cosine-similarity/?";

// Simple Search Form Component
function SimpleSearchForm({ onSearch,loadingState }: { onSearch: (data: any) => void ,loadingState: (loading: boolean) => void}) {
  const [keyword, setKeyword] = useState("");
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState("en");
  const [selectedSort, setSelectedSort] = useState("download_count");
  const [selectedOrder, setSelectedOrder] = useState("ascending");

  const handleSubmit = () => {
    let url = `${urlBaseRequete}sort=${selectedSort}&ord=${selectedOrder}`;
    if (selectedLanguage !== "all") url += `&languages=${selectedLanguage}`;
    if (author) url += `&author_name=${author}`;
    if (title) url += `&title=${title}`;
    if (keyword) url += `&keyword=${keyword}`;
    const fetchBooks = async () => {
      try {
        loadingState(true);
        const response = await fetch(url, { mode: "cors" });
        const result = await response.json();
        onSearch({...result, searchParams: {keyword, title, author}});
      } catch (error) {
      console.error("Error fetching the books:", error);
      }finally{
        loadingState(false);
      }
    };

    fetchBooks();
  
  };

  return (
    <div className="p-6 rounded-lg shadow-md w-full max-w-lg">
      <h2 className="text-xl font-bold mb-4">Simple Search</h2>
      <Input placeholder="Keyword" value={keyword} onChange={(e) => setKeyword(e.target.value)} className="mb-2" />
      <Input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} className="mb-2" />
      <Input placeholder="Author" value={author} onChange={(e) => setAuthor(e.target.value)} className="mb-2" />
      
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div>
          <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
            <SelectTrigger>
              <SelectValue placeholder="Language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fr">French</SelectItem>
              <SelectItem value="en">English</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Select value={selectedSort} onValueChange={setSelectedSort}>
            <SelectTrigger>
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="download_count">Download Count</SelectItem>
              <SelectItem value="closeness">Closeness</SelectItem>
              <SelectItem value="betweenness">Betweenness</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <Select value={selectedOrder} onValueChange={setSelectedOrder}>
            <SelectTrigger>
              <SelectValue placeholder="Order" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ascending">Ascending</SelectItem>
              <SelectItem value="descending">Descending</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <Button onClick={handleSubmit} className="w-full">Search</Button>
    </div>
  );
}

// Advanced Search Form Component
function AdvancedSearchForm({ onSearch,setLoading }: { onSearch: (data: any) => void,setLoading: (loading: boolean) => void}) {
  const [keyword, setKeyword] = useState("");
  const [title, setTitle] = useState("");
  const [selectedTitleType, setSelectedTitleType] = useState("classique");
  const [selectedKeywordType, setSelectedKeywordType] = useState("classique");
  const [selectedLanguage, setSelectedLanguage] = useState("en");
  const [selectedSort, setSelectedSort] = useState("download_count");
  const [selectedOrder, setSelectedOrder] = useState("ascending");
  const [author, setAuthor] = useState("");
  const [selectedAuthorType, setSelectedAuthorType] = useState("classique");

  const handleSubmit = () => {
    let url = urlBaseRequete + "sort=" + selectedSort + "&ord=" + selectedOrder;

    if (selectedLanguage !== "all") {
      url += "&languages=" + selectedLanguage;
    }

    if (author) {
      url += "&author_name=" + author + "&author_name_type=" + selectedAuthorType;
    }

    if (title) {
      url += "&title=" + title + "&title_name_type=" + selectedTitleType;
    }

    if (keyword) {
      url += "&keyword=" + keyword + "&keyword_type=" + selectedKeywordType;
    }

    const fetchBooks = async () => {
      try {
            setLoading(true);
            const response = await fetch(url, { mode: "cors" });
            const result = await response.json();
            onSearch({...result, searchParams: {keyword, title, author}});
      } catch (error) {
            console.error("Error fetching books:", error);
      } finally {
            setLoading(false);
      }
    };

    fetchBooks();
  };

  return (
    <div className="p-6 rounded-lg shadow-md w-full max-w-3xl">
      <h2 className="text-xl font-bold mb-4">Advanced Search</h2>
      
      <div className="mb-4 flex items-center gap-2">
        <div className="flex-1">
          <label className="block text-sm mb-1">Keyword</label>
          <Input 
            placeholder="Enter a keyword" 
            value={keyword} 
            onChange={(e) => setKeyword(e.target.value)} 
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Type</label>
          <Select value={selectedKeywordType} onValueChange={setSelectedKeywordType}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="classique">Classique</SelectItem>
              <SelectItem value="regex">Regex</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="mb-4 flex items-center gap-2">
        <div className="flex-1">
          <label className="block text-sm mb-1">Title</label>
          <Input 
            placeholder="Enter a title" 
            value={title} 
            onChange={(e) => setTitle(e.target.value)} 
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Type</label>
          <Select value={selectedTitleType} onValueChange={setSelectedTitleType}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="classique">Classique</SelectItem>
              <SelectItem value="regex">Regex</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="mb-4 flex items-center gap-2">
        <div className="flex-1">
          <label className="block text-sm mb-1">Author</label>
          <Input 
            placeholder="Enter an author" 
            value={author} 
            onChange={(e) => setAuthor(e.target.value)} 
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Type</label>
          <Select value={selectedAuthorType} onValueChange={setSelectedAuthorType}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="classique">Classique</SelectItem>
              <SelectItem value="regex">Regex</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div className="mb-4 grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm mb-1">Language</label>
          <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
            <SelectTrigger>
              <SelectValue placeholder="Language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fr">French</SelectItem>
              <SelectItem value="en">English</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <label className="block text-sm mb-1">Sort By</label>
          <Select value={selectedSort} onValueChange={setSelectedSort}>
            <SelectTrigger>
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="download_count">Download Count</SelectItem>
              <SelectItem value="closeness">Closeness</SelectItem>
              <SelectItem value="betweenness">Betweenness</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <label className="block text-sm mb-1">Order</label>
          <Select value={selectedOrder} onValueChange={setSelectedOrder}>
            <SelectTrigger>
              <SelectValue placeholder="Order" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ascending">Ascending</SelectItem>
              <SelectItem value="descending">Descending</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <Button onClick={handleSubmit} className="w-full">Search</Button>
    </div>
  );
}

// New TF-IDF Cosine Similarity Search Form Component
function TFIDFCosineSearchForm({ onSearch, setLoading }: { onSearch: (data: any) => void, setLoading: (loading: boolean) => void}) {
  const [keyword, setKeyword] = useState("");
  const [selectedKeywordType, setSelectedKeywordType] = useState("classique");

  const handleSubmit = () => {
    if (!keyword) return;

    const url = `${cosineUrlBase}keyword=${keyword}${selectedKeywordType === "regex" ? "&keyword_type=regex" : ""}`;

    const fetchBooks = async () => {
      try {
        setLoading(true);
        const response = await fetch(url, { mode: "cors" });
        const result = await response.json();
        // Format the result to match the expected structure and add search params
        onSearch({ result: result, suggestions: [], searchParams: {keyword} });
      } catch (error) {
        console.error("Error fetching books with cosine similarity:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchBooks();
  };

  return (
    <div className="p-6 rounded-lg shadow-md w-full max-w-lg">
      <h2 className="text-xl font-bold mb-4">TF-IDF Cosine Search</h2>
      
      <div className="mb-4 flex items-center gap-2">
        <div className="flex-1">
          <label className="block text-sm mb-1">Keyword</label>
          <Input 
            placeholder="Enter a keyword for cosine similarity search" 
            value={keyword} 
            onChange={(e) => setKeyword(e.target.value)} 
          />
        </div>
        <div>
          <label className="block text-sm mb-1">Type</label>
          <Select value={selectedKeywordType} onValueChange={setSelectedKeywordType}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="classique">Classique</SelectItem>
              <SelectItem value="regex">Regex</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <Button 
        onClick={handleSubmit} 
        className="w-full"
        disabled={!keyword}
      >
        Search
      </Button>
      
      <p className="mt-3 text-sm text-gray-500">
        This search finds books with content similar to your keyword using TF-IDF and cosine similarity.
      </p>
    </div>
  );
}

// Book Component with correct image handling
function Book({ book }: { book: any }) {
  return (
    <Dialog>
      <VisuallyHidden>
                  <DialogTitle>Nav Content</DialogTitle>
                </VisuallyHidden>
      <DialogTrigger asChild className=" transition duration-300 ease-in-out hover:scale-[105%]">
        <div className="p-4 border rounded-lg cursor-pointer shadow-md hover:shadow-lg transition-shadow">
          <div className="h-40 w-32 relative mb-2 mx-auto">
            {book.cover_image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img 
                src={book.cover_image} 
                alt={`Cover of ${book.title}`} 
                className="h-full w-full object-cover rounded"
              />
            ) : (
              <div className="h-full w-full bg-gray-200 flex items-center justify-center rounded">
                <span className="text-gray-500">No Cover Found</span>
              </div>
            )}
          </div>
          <h3 className="text-lg font-semibold text-center truncate">{book.title}</h3>
          <p className="text-sm text-center text-gray-600 truncate">
            {book.authors && book.authors.length > 0 ? book.authors[0].name : 'Unknown author'}
          </p>
        </div>
      </DialogTrigger>
      
      <DialogContent className="max-w-md" aria-description="Book details">
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">{book.title}</h2>
          
          {book.authors && book.authors.length > 0 && (
            <div>
              <h3 className="font-semibold">Authors:</h3>
              {book.authors.map((author: any, idx: number) => (
                <p key={idx} className="ml-2">
                  {author.name} {author.birth_year && author.death_year ? `(${author.birth_year} - ${author.death_year})` : ''}
                </p>
              ))}
            </div>
          )}
          
          {book.subjects && book.subjects.length > 0 && (
            <div>
              <h3 className="font-semibold">Subjects:</h3>
              <p className="ml-2">{book.subjects.join(", ")}</p>
            </div>
          )}
          
          {book.languages && book.languages.length > 0 && (
            <div>
              <h3 className="font-semibold">Languages:</h3>
              <p className="ml-2">{book.languages.map((lang: any) => lang.code).join(", ")}</p>
            </div>
          )}
          
          {book.download_count && (
            <div>
              <h3 className="font-semibold">Downloads:</h3>
              <p className="ml-2">{book.download_count}</p>
            </div>
          )}
          
          {book.plain_text && (
            <div className="pt-2">
              <a 
                href={book.plain_text} 
                target="_blank" 
                rel="noopener noreferrer"
                className="bg-foreground  text-background py-2 px-4 rounded inline-block"
              >
                Read the book
              </a>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Helper function to determine which search terms to display
const getSearchTermsString = (searchParams: any) => {
  if (!searchParams) return "";
  
  const terms = [];
  if (searchParams.keyword) terms.push(`keyword "${searchParams.keyword}"`);
  if (searchParams.title) terms.push(`title "${searchParams.title}"`);
  if (searchParams.author) terms.push(`author "${searchParams.author}"`);
  
  if (terms.length === 0) return "";
  return terms.join(", ");
};

export default function HomePgae() {
  const [bookData, setBookData] = useState({ 
    result: [], 
    suggestions: [],
    searchParams: null,
    hasSearched: false // Track if a search has been performed
  });
  const [loading, setLoading] = useState(false);
  
  // Update the setBookData to track if a search has been made
  const handleSetBookData = (data: any) => {
    setBookData({
      ...data,
      hasSearched: true // Mark that a search has been performed
    });
  };

  // Search terms string for display
  const searchTermsString = getSearchTermsString(bookData.searchParams);

  return (
    <div>
  
      <Button 
        onClick={() => window.location.href = "/"} 
        className="flex border 
                    border-foreground bg-background text-foreground 
                    mt-4 mx-auto items-center justify-center transition-colors duration-200"
      >
         <Home size={32} />
        </Button>
      <div className="container mx-auto px-4 py-6">
        <Tabs defaultValue="simple" className="w-full">
          <div className="flex justify-center mb-4">
            <TabsList>
              <TabsTrigger value="simple">Simple Search</TabsTrigger>
              <TabsTrigger value="advanced">Advanced Search</TabsTrigger>
              <TabsTrigger value="tfidf">TF-IDF Cosine</TabsTrigger>
            </TabsList>
          </div>
          
          <TabsContent value="simple" className="flex justify-center">
            <SimpleSearchForm onSearch={handleSetBookData} loadingState={setLoading} />
          </TabsContent>
          
          <TabsContent value="advanced" className="flex justify-center">
            <AdvancedSearchForm onSearch={handleSetBookData} setLoading={setLoading}/>
          </TabsContent>
          
          <TabsContent value="tfidf" className="flex justify-center">
            <TFIDFCosineSearchForm onSearch={handleSetBookData} setLoading={setLoading}/>
          </TabsContent>
        </Tabs>
         
        {/* Loading indicator */}
        {loading && (
          <div className="mt-8 flex justify-center items-center">
            <Loader />
          </div>
        )}
        
        <div className="mt-12 space-y-10">
          {/* Results section with book count */}
          {!loading && bookData.result && bookData.result.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">
                Results {bookData.result.length > 0 && `(${bookData.result.length} books found)`}
                {searchTermsString && <span className="block text-lg font-normal mt-1">Related to {searchTermsString}</span>}
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {bookData.result.map((book: any, index: number) => (
                  <Book key={index} book={book} />
                ))}
              </div>
            </div>
          )}
          
          {/* Suggestions section with book count */}
          {!loading && bookData.suggestions && bookData.suggestions.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">
                You Might Also Like {bookData.suggestions.length > 0 && `(${bookData.suggestions.length} books)`}
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {bookData.suggestions.map((book: any, index: number) => (
                  <Book key={index} book={book} />
                ))}
              </div>
            </div>
          )}
          
          {/* No books found state (only show when a search was performed) */}
          {!loading && bookData.hasSearched && 
           bookData.result.length === 0 && 
           bookData.suggestions.length === 0 && (
            <div className="mt-8 flex justify-center items-center">
              <div className="p-4 rounded-lg bg-primary/10 text-primary font-medium">
                No books found
              </div>
            </div>
          )}
          
          {/* Initial state (before any search) */}
          {!loading && !bookData.hasSearched && (
            <div className="mt-8 flex flex-col justify-center items-center text-center">
              <div className="p-8 rounded-lg bg-primary/5 text-primary">
                <h3 className="text-xl font-medium mb-2">Search your favorite books</h3>
                <p className="text-base text-foreground/80">
                  Use the search forms above to discover books by title, author, or keyword
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}