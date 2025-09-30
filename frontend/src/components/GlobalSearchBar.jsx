import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api';

// A simple debounce hook
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  return debouncedValue;
};

const GlobalSearchBar = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const searchRef = useRef(null);
  const navigate = useNavigate();

  const performSearch = useCallback(async (searchQuery) => {
    if (searchQuery.length < 2) {
      setResults(null);
      setIsOpen(false);
      return;
    }
    setLoading(true);
    try {
      const response = await apiClient.get('/v1/network/search', { params: { q: searchQuery } });
      const data = response.data;
      setResults(data);
      setIsOpen(true);
    } catch (error) {
      console.error('Search failed:', error);
      setResults(null);
      setIsOpen(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    performSearch(debouncedQuery);
  }, [debouncedQuery, performSearch]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleResultClick = (url) => {
    setQuery('');
    setResults(null);
    setIsOpen(false);
    navigate(`/dashboard${url}`);
  };

  const renderResults = () => {
    if (!results) return null;

    const allResults = [
      ...(results.devices || []),
      ...(results.incidents || []),
      ...(results.policies || []),
      ...(results.topology_devices || []),
    ];

    if (allResults.length === 0) {
      return <div className="noResults">No results found for "{debouncedQuery}"</div>;
    }

    const resultCategories = [
      { title: 'Monitoring Devices', items: results.devices },
      { title: 'Incidents', items: results.incidents },
      { title: 'QoS Policies', items: results.policies },
      { title: 'Topology Devices', items: results.topology_devices },
    ];

    return (
      <>
        {resultCategories.map(category => (
          category.items && category.items.length > 0 && (
            <div key={category.title} className="category">
              <h4>{category.title}</h4>
              {category.items.map(item => (
                <div key={`${item.type}-${item.id}`} className="resultItem" onClick={() => handleResultClick(item.url)}>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </div>
              ))}
            </div>
          )
        ))}
      </>
    );
  };

  return (
    <div className="searchContainer" ref={searchRef}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query.length >= 2 && setIsOpen(true)}
        placeholder="Global search..."
        className="searchInput"
      />
      {loading && <div className="spinner"></div>}
      {isOpen && (
        <div className="resultsDropdown">
          {loading && !results ? <div className="loadingText">Searching...</div> : renderResults()}
        </div>
      )}
    </div>
  );
};

export default GlobalSearchBar;