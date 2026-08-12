import { useState, useMemo } from 'react';
import ArticleCard from '../components/ArticleCard';
import { TransitionLink } from '../components/TransitionContext';
import { BROWSE_ARTIFACTS, FILTER_COUNTS } from '../data/artifacts';

export default function Browse() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');

  /* ── Sidebar multi-select state ── */
  const [selectedRegions, setSelectedRegions]   = useState([]);
  const [selectedPeriods, setSelectedPeriods]   = useState([]);
  const [selectedArtForms, setSelectedArtForms] = useState([]);

  /* ── Accordion ── */
  const [openAccordions, setOpenAccordions] = useState({
    region: true, period: false, artForm: false,
  });
  const toggleAccordion = (key) =>
    setOpenAccordions((prev) => ({ ...prev, [key]: !prev[key] }));

  /* ── Toggle checkbox helpers ── */
  const toggleItem = (setter, val) =>
    setter((prev) =>
      prev.includes(val) ? prev.filter((v) => v !== val) : [...prev, val]
    );

  /* ── Filter chips ── */
  const filterChips = [
    { id: 'all',      label: 'All'      },
    { id: 'warli',    label: 'Warli'    },
    { id: 'gond',     label: 'Gond'     },
    { id: 'mughal',   label: 'Mughal'   },
    { id: 'buddhist', label: 'Buddhist' },
    { id: 'chola',    label: 'Chola'    },
    { id: 'rajput',   label: 'Rajput'   },
  ];

  const REGIONS   = ['Maharashtra', 'Rajasthan', 'Tamil Nadu', 'Madhya Pradesh'];
  const PERIODS   = ['Ancient (pre-500 CE)', 'Medieval (500–1500 CE)', 'Early Modern (1500–1800)', 'Contemporary'];
  const ART_FORMS = ['Sculpture', 'Painting', 'Manuscript', 'Textile'];

  /* ── Combined filter logic ── */
  const filteredArtifacts = useMemo(() => {
    return BROWSE_ARTIFACTS.filter((art) => {
      const q = searchQuery.toLowerCase();
      const matchSearch =
        art.title.toLowerCase().includes(q) ||
        art.type.toLowerCase().includes(q) ||
        art.period.toLowerCase().includes(q) ||
        (art.description || '').toLowerCase().includes(q);

      // Chip filter: 'all' shows everything, otherwise match art.filter OR check if
      // chip label matches the art's filter category
      const matchChip = selectedFilter === 'all' || art.filter === selectedFilter;

      // Sidebar: if any checkboxes selected, artifact must match at least one in each
      // non-empty group (AND between groups, OR within group)
      const matchRegion  = selectedRegions.length === 0  || selectedRegions.includes(art.region);
      const matchPeriod  = selectedPeriods.length === 0  || selectedPeriods.includes(art.timePeriod);
      const matchArtForm = selectedArtForms.length === 0 || selectedArtForms.includes(art.artForm);

      return matchSearch && matchChip && matchRegion && matchPeriod && matchArtForm;
    });
  }, [searchQuery, selectedFilter, selectedRegions, selectedPeriods, selectedArtForms]);

  const countText = useMemo(() => {
    const hasActiveFilter =
      searchQuery || selectedFilter !== 'all' ||
      selectedRegions.length || selectedPeriods.length || selectedArtForms.length;
    if (hasActiveFilter) return `Showing ${filteredArtifacts.length} results`;
    return `Showing ${FILTER_COUNTS[selectedFilter] ?? '1,204'} artifacts`;
  }, [selectedFilter, searchQuery, filteredArtifacts.length, selectedRegions, selectedPeriods, selectedArtForms]);

  const handleReset = () => {
    setSearchQuery('');
    setSelectedFilter('all');
    setSelectedRegions([]);
    setSelectedPeriods([]);
    setSelectedArtForms([]);
  };

  const hasActiveFilters =
    selectedRegions.length || selectedPeriods.length || selectedArtForms.length;

  return (
    <main className="pt-20 pb-[120px] bg-[#fbf9f5] min-h-screen text-[#1b1c1a]"
          aria-label="Browse collection">
      <div className="w-full max-w-[1280px] mx-auto px-5 md:px-20 pt-[60px] pb-[120px] flex flex-col gap-12">

        {/* ── Header ── */}
        <header className="w-full flex flex-col gap-8">
          <div className="flex items-center w-full">
            <h1 className="font-['Playfair_Display'] text-[14px] font-medium uppercase tracking-widest text-[#1b1c1a] whitespace-nowrap mr-6">
              BROWSE THE COLLECTION
            </h1>
            <div className="h-px bg-[#d1c5b2] flex-grow" />
          </div>

          {/* Search */}
          <div className="relative w-full max-w-4xl">
            <span className="material-symbols-outlined absolute left-0 top-1/2 -translate-y-1/2 text-[#807665]">search</span>
            <input
              className="w-full bg-transparent border-0 border-b border-[#d1c5b2] py-4 pl-8 pr-4 text-[18px] text-[#1b1c1a] focus:outline-none focus:border-[#8b6914] transition-colors placeholder:text-[#807665]/70"
              placeholder="Search by era, material, or keyword..."
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search artifacts"
            />
          </div>

          {/* Filter chips */}
          <div className="w-full overflow-x-auto no-scrollbar pb-2">
            <div className="flex gap-3 items-center min-w-max">
              {filterChips.map((chip) => (
                <button
                  key={chip.id}
                  onClick={() => setSelectedFilter(chip.id)}
                  className={`px-5 py-2 rounded-full border border-[#d1c5b2] text-[12px] font-medium uppercase tracking-wider transition-colors ${
                    selectedFilter === chip.id
                      ? 'bg-[#1b1c1a] text-[#fbf9f5] border-[#1b1c1a]'
                      : 'text-[#4e4637] hover:border-[#1b1c1a]'
                  }`}
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        </header>

        {/* ── Sidebar + Content ── */}
        <div className="flex flex-col md:flex-row gap-6 items-start w-full">

          {/* Filter sidebar */}
          <aside className="w-full md:w-64 flex-shrink-0" aria-label="Filters">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-[#d1c5b2]">
              <h2 className="font-['Playfair_Display'] text-[12px] font-semibold uppercase tracking-widest text-[#1b1c1a]">
                Filters
                {hasActiveFilters > 0 && (
                  <span className="ml-2 px-1.5 py-0.5 bg-[#8b6914] text-white text-[9px] rounded-full">
                    {(selectedRegions.length + selectedPeriods.length + selectedArtForms.length)}
                  </span>
                )}
              </h2>
              <button onClick={handleReset} className="text-[#807665] hover:text-[#1b1c1a] text-[12px] font-medium transition-colors">Reset</button>
            </div>

            <div className="flex flex-col gap-2">
              {/* Region accordion */}
              <div className="border-b border-[#d1c5b2] pb-2">
                <button
                  onClick={() => toggleAccordion('region')}
                  className="flex items-center justify-between w-full text-left text-[16px] text-[#1b1c1a] py-3 hover:text-[#8b6914] transition-colors"
                  aria-expanded={openAccordions.region}
                >
                  <span>Region</span>
                  <span className={`material-symbols-outlined text-[#807665] transition-transform duration-300 ${openAccordions.region ? 'rotate-180' : ''}`}>
                    expand_more
                  </span>
                </button>
                {openAccordions.region && (
                  <div className="py-3 space-y-2 pl-2">
                    {REGIONS.map((item) => (
                      <label key={item} className="flex items-center gap-2 text-sm text-[#4e4637] cursor-pointer hover:text-[#1b1c1a] transition-colors">
                        <input
                          type="checkbox"
                          className="accent-[#8b6914]"
                          checked={selectedRegions.includes(item)}
                          onChange={() => toggleItem(setSelectedRegions, item)}
                        />
                        {item}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Time Period accordion */}
              <div className="border-b border-[#d1c5b2] pb-2">
                <button
                  onClick={() => toggleAccordion('period')}
                  className="flex items-center justify-between w-full text-left text-[16px] text-[#1b1c1a] py-3 hover:text-[#8b6914] transition-colors"
                  aria-expanded={openAccordions.period}
                >
                  <span>Time Period</span>
                  <span className={`material-symbols-outlined text-[#807665] transition-transform duration-300 ${openAccordions.period ? 'rotate-180' : ''}`}>
                    expand_more
                  </span>
                </button>
                {openAccordions.period && (
                  <div className="py-3 space-y-2 pl-2">
                    {PERIODS.map((item) => (
                      <label key={item} className="flex items-center gap-2 text-sm text-[#4e4637] cursor-pointer hover:text-[#1b1c1a] transition-colors">
                        <input
                          type="checkbox"
                          className="accent-[#8b6914]"
                          checked={selectedPeriods.includes(item)}
                          onChange={() => toggleItem(setSelectedPeriods, item)}
                        />
                        {item}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Art Form accordion */}
              <div className="border-b border-[#d1c5b2] pb-2">
                <button
                  onClick={() => toggleAccordion('artForm')}
                  className="flex items-center justify-between w-full text-left text-[16px] text-[#1b1c1a] py-3 hover:text-[#8b6914] transition-colors"
                  aria-expanded={openAccordions.artForm}
                >
                  <span>Art Form</span>
                  <span className={`material-symbols-outlined text-[#807665] transition-transform duration-300 ${openAccordions.artForm ? 'rotate-180' : ''}`}>
                    expand_more
                  </span>
                </button>
                {openAccordions.artForm && (
                  <div className="py-3 space-y-2 pl-2">
                    {ART_FORMS.map((item) => (
                      <label key={item} className="flex items-center gap-2 text-sm text-[#4e4637] cursor-pointer hover:text-[#1b1c1a] transition-colors">
                        <input
                          type="checkbox"
                          className="accent-[#8b6914]"
                          checked={selectedArtForms.includes(item)}
                          onChange={() => toggleItem(setSelectedArtForms, item)}
                        />
                        {item}
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </aside>

          {/* ── Main content ── */}
          <div className="flex-grow w-full flex flex-col gap-8">
            {/* Sort bar */}
            <div className="flex items-center justify-between w-full pb-2">
              <span className="text-[16px] text-[#807665]">{countText}</span>
              <div className="relative flex items-center">
                <select
                  className="appearance-none bg-transparent border-0 border-b border-[#d1c5b2] py-2 pl-2 pr-8 text-[16px] text-[#1b1c1a] focus:outline-none cursor-pointer"
                  aria-label="Sort results"
                >
                  <option>Sort by Relevance</option>
                  <option>Date Added (Newest)</option>
                  <option>Alphabetical (A-Z)</option>
                </select>
                <span className="material-symbols-outlined absolute right-0 top-1/2 -translate-y-1/2 text-[#807665] pointer-events-none">arrow_drop_down</span>
              </div>
            </div>

            {filteredArtifacts.length === 0 ? (
              <div className="text-center py-20">
                <p className="font-['Playfair_Display'] text-[24px] italic text-[#807665]">
                  No artifacts found matching your filters.
                </p>
                <button onClick={handleReset} className="mt-6 px-6 py-2 border border-[#1b1c1a] rounded font-semibold text-sm text-[#1b1c1a] hover:bg-[#1b1c1a] hover:text-[#fbf9f5] transition-all">
                  Clear Filters
                </button>
              </div>
            ) : (
              <>
                {/* Staggered article grid */}
                <div className="article-grid">
                  {filteredArtifacts.map((art, i) => (
                    <ArticleCard key={art.id} article={art} index={i} />
                  ))}
                </div>

                <div className="w-full flex justify-center mt-8">
                  <button className="px-8 py-3 rounded border border-[#1b1c1a] font-semibold text-[16px] hover:bg-[#1b1c1a] hover:text-[#fbf9f5] transition-colors duration-300">
                    Load More Artifacts
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-[#f5f3ef] border-t border-[#d1c5b2] py-16">
        <div className="max-w-[1280px] mx-auto px-5 md:px-20 flex flex-col md:flex-row justify-between items-center gap-8">
          <span className="font-['Playfair_Display'] text-[24px] italic text-[#1b1c1a] opacity-80">ARKANA.</span>
          <div className="flex gap-6 text-[14px]">
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">About</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Privacy</TransitionLink>
            <TransitionLink to="/" className="text-[#4e4637] hover:text-[#8b6914] transition-colors">Contact</TransitionLink>
          </div>
          <p className="text-[14px] text-[#807665]">© 2026 ARKANA. Preserving India's Cultural Legacy.</p>
        </div>
      </footer>
    </main>
  );
}
