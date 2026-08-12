/**
 * ARKANA — Demo AI Chat Response Engine
 *
 * Simulates the RAG pipeline output format:
 *   { text, citation, insightCard, mapEvent }
 *
 *   { text, citation, insightCard, mapEvent, geoData }
 *
 * geoData shapes:
 *   { type: 'marker', lat, lng, label, zoom }
 *   { type: 'markers', points: [{lat,lng,label,color}], zoom, center }
 *   { type: 'region', polygon: [[lat,lng],...], label, color, zoom, center, markers }
 */

export const DEMO_KNOWLEDGE_BASE = [
  // ── Taj Mahal ─────────────────────────────────────────────────────────────
  {
    keywords: ['taj mahal', 'taj', 'agra', 'mumtaz', 'mausoleum'],
    text: `The Taj Mahal (1631–1648 CE) stands on the southern bank of the Yamuna river in Agra, Uttar Pradesh. Commissioned by Mughal Emperor Shah Jahan as an eternal mausoleum for his beloved wife Mumtaz Mahal, it is widely considered the world's finest example of Mughal architecture.\n\nThe complex took approximately 22 years, 20,000 workers, and artisans from Persia, the Ottoman Empire, and Europe to complete. The central dome rises 73 metres above the surrounding gardens. The entire exterior is clad in white Makrana marble from Rajasthan, inlaid with precious and semi-precious stones (pietra dura) in floral and geometric patterns.\n\nThe four flanking minarets are slightly tilted outward — a deliberate engineering choice so that in the event of an earthquake they would fall away from the main tomb. The Taj Mahal was inscribed as a UNESCO World Heritage Site in 1983 and is visited by over 7 million tourists annually.`,
    citation: 'TM-1',
    source: 'Archaeological Survey of India — Taj Mahal Conservation Report',
    insightCard: {
      title: 'Taj Mahal, Agra',
      period: '1631–1648 CE · Mughal Empire',
      image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Taj_Mahal%2C_Agra%2C_India_edit3.jpg/640px-Taj_Mahal%2C_Agra%2C_India_edit3.jpg',
      link: '/artifact',
    },
    mapEvent: { pinId: 'delhi' },
    geoData: {
      type: 'marker',
      lat: 27.1751,
      lng: 78.0421,
      label: 'Taj Mahal — Agra, Uttar Pradesh',
      zoom: 13,
    },
  },

  // ── Warli ─────────────────────────────────────────────────────────────────
  {
    keywords: ['warli', 'warli art', 'tribal art', 'maharashtra', 'adivasi painting', 'sahyadri'],
    text: `Warli art originates from the Warli tribe of Maharashtra's Sahyadri mountain range. Dating back to at least the 10th century CE, it is one of India's oldest surviving artistic traditions.\n\nPainted on mud walls using rice paste and bamboo sticks, Warli compositions consist of geometric shapes — circles, triangles, and squares — combined to depict scenes of daily village life: harvests, weddings, the Tarpa dance, and the forest deity Palghat. The circle represents the sun and moon; the triangle is derived from mountains and pointed trees; the square denotes sacred enclosures.\n\nUnlike most classical Indian art forms, Warli was historically created exclusively by women called "suvasinis" during marriage ceremonies. Modern masters such as Jivya Soma Mashe brought it to international recognition in the 1970s.`,
    citation: '1',
    source: 'Tribal Cultural Heritage in India Foundation — Warli Art Traditions',
    insightCard: {
      title: 'Warli Village Life',
      period: 'Late 20th Century · Maharashtra',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCrlSg9rTQBUQedvSUodw2bobu8pP6v3ohiYwJ4xQa4_eQ-gSja2_B8LbCpXNnfVSPauGKwxje3W6kjl_CTxsLE7zofu-PhZUHE4osTznSPJ-yi4I0AGGhLr-Rl1phwgWv5jrrsQvAKmEvlyi_yBXrrrwMtDp1Gzl1XG1sLPUhvbtuej7PYCzjlHM20nQPi5kw957zXcaUhNlFgrPuONtllAtw1AEeNKbiJXD5nDEQ6w1esn6hEO16T-SV-fPaAPyMHpU_Qap_Fyw',
      link: '/culture',
    },
    mapEvent: { pinId: 'maharashtra', label: 'Maharashtra' },
    geoData: {
      type: 'region',
      label: 'Sahyadri Region — Warli Heartland',
      color: '#c0770a',
      center: [19.7, 73.2],
      zoom: 8,
      polygon: [
        [20.5, 72.5], [20.6, 73.2], [20.2, 73.8], [19.5, 73.8],
        [19.0, 73.5], [19.0, 72.8], [19.5, 72.6], [20.5, 72.5]
      ],
      markers: [
        { lat: 19.9975, lng: 73.7898, label: 'Nashik — Warli art transition', color: '#c0770a' },
        { lat: 20.0059, lng: 72.8321, label: 'Palghar — Adivasi communities', color: '#c0770a' },
        { lat: 19.4586, lng: 72.8054, label: 'Dahanu — Jivya Soma Mashe\'s home', color: '#a05c08' },
      ],
    },
  },

  // ── Gond ──────────────────────────────────────────────────────────────────
  {
    keywords: ['gond', 'gond art', 'madhya pradesh', 'digna', 'gondi', 'bhopal', 'jangarh'],
    text: `Gond art is a form of folk and tribal art originating from the Gond community of central India, primarily Madhya Pradesh, Chhattisgarh, Odisha, and Andhra Pradesh.\n\nTraditionally, Gond patterns called "Digna" were painted on floors and walls of homes to invite good luck. The art is characterised by intricate lines, dots, and dashes that fill every contour of an image — animals, trees, birds — creating a vibrating visual texture. According to Gond belief, viewing a good image brings good luck to the viewer.\n\nJangarh Singh Shyam is widely credited with transitioning Gond art from wall murals to paper and canvas in the 1980s, under the mentorship of artist J. Swaminathan at Bharat Bhavan, Bhopal. Today, artists like Venkat Raman Singh Shyam carry this tradition internationally.`,
    citation: '2',
    source: 'Bharat Bhavan Archives — Gond Tribal Arts Documentation',
    insightCard: {
      title: 'Gond Deer Composition',
      period: 'Contemporary · Madhya Pradesh',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBNqbvwQFgB4itIMpaaMeC7kAlkHDySh0WhIaJoZZV9ZCB-A8QZm6tmcJobLHdasgmi_q-bTZXoYnIzr33teLJHvplnjdPM4GoFJqgFdXFal7qYNdw_B8KDtRfIytMssI2J9N1Mb5kGoY_URbZVT_zufvROqhsTDQSUP74sdlZk_ka7JRX42txQokwotSGuB32Y97f3f7d9rPOo81G4DqlCx9pSOWbvbhw6K-Zc0z9xp0kBgPy4jwYKoh4XOjUKcv-9dWTC8_GLew',
      link: '/artifact',
    },
    mapEvent: { pinId: 'mp', label: 'Madhya Pradesh' },
    geoData: {
      type: 'region',
      label: 'Gondwana Region (Central India)',
      color: '#2e7d32',
      center: [22.5, 80.0],
      zoom: 6,
      polygon: [
        [24.5, 76.5], [24.8, 81.5], [23.5, 84.0], [21.0, 83.5],
        [19.0, 81.5], [19.5, 78.5], [21.5, 77.0], [23.0, 77.2], [24.5, 76.5]
      ],
      markers: [
        { lat: 23.2599, lng: 77.4126, label: 'Bhopal — Bharat Bhavan museum', color: '#2e7d32' },
        { lat: 21.8974, lng: 82.9076, label: 'Bastar — Gond traditional crafts', color: '#1b5e20' },
        { lat: 23.8315, lng: 80.0148, label: 'Mandla — Central tribal forest belt', color: '#2e7d32' },
      ],
    },
  },

  // ── Chola Bronzes ─────────────────────────────────────────────────────────
  {
    keywords: ['chola', 'nataraja', 'bronze', 'chola dynasty', 'tamil', 'tamil nadu', 'lost wax', 'cire perdue', 'thanjavur', 'tandava'],
    text: `The Chola dynasty (9th–13th centuries CE) produced some of the finest bronze sculptures ever created. Using the ancient lost-wax (cire perdue) casting technique, Chola artisans achieved remarkable detail and spiritual expression.\n\nThe iconic Nataraja — Shiva as the Lord of Dance — is the dynasty's supreme artistic achievement. Cast in Panchaloka (an alloy of five metals: gold, silver, copper, iron, and lead), the figure stands within a ring of fire (prabhamandala), one foot raised in the Ananda Tandava pose. Every element is symbolic: the upper right hand holds a damaru (drum of creation), the upper left holds agni (flame of destruction), the lower right is in abhaya mudra (protection), and the lower left points to the raised foot (liberation).\n\nThe Chola Nataraja at the National Museum, New Delhi (11th century) and those at Thanjavur Art Gallery are considered masterpieces of world sculpture.`,
    citation: '3',
    source: 'Archaeological Survey of India — Chola Bronze Iconography',
    insightCard: {
      title: 'Chola Nataraja Bronze',
      period: '11th Century CE · Tamil Nadu',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCLeOoA-2V4sDuQgzGvGudPvWMa2VP6CqbfkCXZ47iTrVEWtwqcXU_YwoEjH4gWzByCAIsO1O8ajeRLWUBotHeLE2Q7WpJJYevQPbrBIHIwwz9uVFJg0DzPYL8F79yY1UoRCrVtQ012WAPhEIi5ODq5byXZyJfB9vj3Y0UIymtEIkWNYv0JDgWJtnadAE0XqHMTRCEDj__VHdG8f6YoPafGUh5zPqSaMRk6FWeDH8FZ5w6V94r_69OHEwWlLcA7FfVHLjYUlzZ3fw',
      link: '/artifact',
    },
    mapEvent: { pinId: 'tn', label: 'Tamil Nadu' },
    geoData: {
      type: 'region',
      label: 'Chola Empire Peak Territory (c. 1030 CE)',
      color: '#8b6914',
      center: [11.5, 79.0],
      zoom: 6,
      polygon: [
        [15.5, 78.0], [16.5, 81.0], [14.0, 80.5], [11.0, 80.0],
        [9.0, 79.5], [8.0, 77.5], [9.5, 76.5], [12.5, 75.0],
        [14.5, 75.5], [15.5, 78.0]
      ],
      markers: [
        { lat: 10.7905, lng: 79.1398, label: 'Thanjavur — Chola Capital & Art Centre', color: '#8b6914' },
        { lat: 11.2078, lng: 79.4475, label: 'Gangaikonda Cholapuram — Imperial Temple', color: '#8b6914' },
        { lat: 11.9416, lng: 79.8083, label: 'Chidambaram — Cosmic Dance Temple', color: '#8b6914' },
        { lat: 10.3528, lng: 79.3620, label: 'Kumbakonam — Bronze Casting Atelier', color: '#a07010' },
      ],
    },
  },

  // ── Mughal Empire ─────────────────────────────────────────────────────────
  {
    keywords: ['mughal', 'miniature', 'akbar', 'jahangir', 'mughal empire', 'mughal architecture', 'red fort', 'humayun'],
    text: `The Mughal Empire (1526–1857) fostered a golden age of artistic synthesis, blending Persian, Central Asian, and indigenous Rajput traditions into a distinctly Indian aesthetic.\n\nMughal miniature painting flourished under Emperor Akbar, who established the imperial atelier (karkhana) and invited Persian masters Mir Sayyid Ali and Abd al-Samad. The Hamzanama — a 1,400-folio illustrated manuscript — stands as one of the most ambitious artistic projects of the 16th century.\n\nUnder Jahangir, portraiture and naturalistic study reached their zenith. The emperor famously commissioned detailed observations of flowers, birds, and animals, producing works of near-scientific accuracy. The painting "Emperor Jahangir Holding a Globe" (c. 1614) exemplifies the period's blend of symbolic allegory and refined craftsmanship.\n\nMughal architecture culminated in the Taj Mahal (1631–1648), a UNESCO World Heritage Site built by Shah Jahan as a mausoleum for Empress Mumtaz Mahal.`,
    citation: '4',
    source: 'National Museum New Delhi — Mughal Arts Collection Catalogue',
    insightCard: {
      title: 'Emperor Jahangir Holding a Globe',
      period: 'c. 1614 · Mughal Empire',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCkwj_WIvD_U_ktgHWB71RA5c6eiCUNU1fX7Jyb-Y1Hdm14_u2Hos3Lz1nVZ-yVW_Av-N_c500HFT2vtm5Jy2q4gKdDJ5WjAWgJnxGvRVrSuhWHOP8pS4lloB5NxFVn9NJu1PBLbBtr_j5BN736FwvB8fSQ52FDl8CyUmwYi6LGFQVI8--laKzaGhBmNbJDkLzI8aSLbdKSPt_AcS1RyNXknnnj_HuQKUqUcYED7eypiFiHuChHrKj8pULvHBHpYfooH4R3mFkrhQ',
      link: '/artifact',
    },
    mapEvent: { pinId: 'delhi', label: 'Delhi' },
    geoData: {
      type: 'region',
      label: 'Mughal Empire at Zenith (c. 1700 CE)',
      color: '#7b1fa2',
      center: [24.0, 77.0],
      zoom: 5,
      polygon: [
        [35.0, 68.0], [36.0, 74.0], [32.0, 78.0], [28.0, 85.0],
        [26.0, 92.0], [22.0, 90.0], [18.0, 82.0], [15.0, 78.0],
        [18.0, 73.0], [22.0, 69.0], [26.0, 67.0], [31.5, 66.0], [35.0, 68.0]
      ],
      markers: [
        { lat: 28.6139, lng: 77.2090, label: 'Delhi — Red Fort & Capital', color: '#7b1fa2' },
        { lat: 27.1751, lng: 78.0421, label: 'Agra — Taj Mahal and Imperial Court', color: '#9c27b0' },
        { lat: 27.0949, lng: 77.6612, label: 'Fatehpur Sikri — Akbar\'s Capital City', color: '#7b1fa2' },
        { lat: 31.5204, lng: 74.3587, label: 'Lahore — Badshahi Mosque & Gardens', color: '#8e24aa' },
        { lat: 19.8762, lng: 75.3433, label: 'Aurangabad — Aurangzeb\'s Deccan Capital', color: '#6a0080' },
      ],
    },
  },

  // ── Ashokan Pillars / Maurya ───────────────────────────────────────────────
  {
    keywords: ['ashoka', 'ashokan', 'pillar', 'maurya', 'mauryan', 'brahmi', 'dhamma', 'edict', 'lion capital', 'sarnath'],
    text: `The Ashokan Pillars were erected by Emperor Ashoka of the Maurya dynasty during the 3rd century BCE, following his conversion to Buddhism after the Kalinga War (c. 261 BCE). The war's unprecedented carnage — an estimated 100,000 deaths — transformed Ashoka from a conqueror into a dharmic ruler.\n\nThe pillars, typically 40–50 feet tall and monolithic (carved from single sandstone blocks), bear edicts in Brahmi script detailing Ashoka's policies of Dhamma: non-violence (ahimsa), religious tolerance, welfare of subjects, and protection of animals.\n\nThe Lion Capital of Ashoka, discovered at Sarnath (now in the Sarnath Museum), was adopted as India's national emblem in 1950. The Ashoka Chakra from this capital appears at the centre of the Indian national flag. The pillar at Vaishali is the only Ashokan pillar still standing at its original site with its original capital intact.`,
    citation: '5',
    source: 'Archaeological Survey of India — Mauryan Period Monuments',
    insightCard: {
      title: 'Ashokan Pillar Fragment',
      period: '3rd Century BCE · Maurya Empire',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC4GiUO8DnCPkZiHnNW5Tmstim5dcTAiKAtm9bi72Hap9GEURhywdMcZtYZP7P3mMtn_YbwP2ysP9mG-eB5Cgagv6skn0J_9ruQMakIXyb_i6giRqGz-_0klySrnr1kyupeE8BVWkdZ8wQFLeCPfLxdx4eXKrXlHwMpPJTuxL34Lx2qnmK5885rNsRqfzUXYgaXXj2DHthPgRMIdpMN5w3_hgC13Q586EMUflva30TeOeNg5MbXF1sD-AQmm9-Fn2OpxvKcsr3Edg',
      link: '/artifact',
    },
    mapEvent: null,
    geoData: {
      type: 'region',
      label: 'Maurya Empire Maximum Extent (c. 250 BCE)',
      color: '#b45309',
      center: [23.5, 78.0],
      zoom: 5,
      polygon: [
        [35.0, 65.0], [36.0, 72.0], [34.0, 78.0], [28.0, 88.0],
        [26.0, 94.0], [22.0, 91.0], [16.0, 80.0], [13.0, 78.0],
        [13.0, 76.5], [16.0, 74.0], [21.0, 69.0], [26.0, 65.0], [35.0, 65.0]
      ],
      markers: [
        { lat: 25.3754, lng: 82.9876, label: 'Sarnath — Lion Capital Edict', color: '#b45309' },
        { lat: 26.1204, lng: 85.3647, label: 'Vaishali — Monolithic Pillar Site', color: '#b45309' },
        { lat: 23.4820, lng: 77.7378, label: 'Sanchi — Great Stupa Foundations', color: '#b45309' },
        { lat: 25.6126, lng: 85.1589, label: 'Pataliputra — Imperial Maurya Capital', color: '#92400e' },
      ],
    },
  },

  // ── Indus Valley Civilisation ─────────────────────────────────────────────
  {
    keywords: ['indus', 'indus valley', 'harappa', 'mohenjo-daro', 'mohenjo daro', 'harappan', 'pashupati', 'civilization', 'civilisation', 'dholavira', 'rakhigarhi'],
    text: `The Indus Valley Civilisation (c. 3300–1300 BCE), also known as the Harappan civilisation, flourished across what is now Pakistan and northwest India. At its peak (c. 2600–1900 BCE), it was the largest of the four ancient urban civilisations, exceeding Egypt and Mesopotamia in geographic extent.\n\nHarappan cities — Mohenjo-daro, Harappa, Dholavira, Rakhigarhi — featured sophisticated urban planning: grid-pattern streets, standardised brick sizes, an advanced drainage system, and multi-storey structures. The Great Bath at Mohenjo-daro is considered one of the earliest examples of a public water tank.\n\nThe Pashupati Seal, a steatite tablet discovered at Mohenjo-daro, depicts a seated, possibly three-faced figure surrounded by animals — often interpreted as a proto-Shiva or master of animals. The Indus script, inscribed on over 4,000 artefacts, remains undeciphered, making it one of archaeology's greatest open questions.`,
    citation: '6',
    source: 'National Museum New Delhi — Harappan Civilisation Gallery',
    insightCard: {
      title: 'Pashupati Seal',
      period: '2600 BCE · Indus Valley',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBGQV477gjNMtujTxsK3aZyG0CMVoSFz8psLqJ0L53DHa3-vo4ZAIK09V-Gjb5KB1RtxVHWkrqDVHbi6giDZpkmk1m93kDKaGjo_OwFuk-Y7e7ckV59WI5p_0E2oxTyAGP_YuxlL2Ju0VviCGgsDtPUVhWP_p9JGpRQdZ-VRVyu1luNPjX-dBlt_tTzbJVVgyXKZjoiIQe5cDV2KEPk9q2xng6kQeZpMd2PPcjYj67Z4aoQCkhyE-SdL5tZKr4KtllBv2rYJuXhZQ',
      link: '/artifact',
    },
    mapEvent: null,
    geoData: {
      type: 'region',
      label: 'Indus Valley Civilisation (c. 3300–1300 BCE)',
      color: '#d97706',
      center: [27.5, 69.0],
      zoom: 5,
      polygon: [
        [37.0, 60.0], [37.5, 65.0], [36.5, 70.0], [34.0, 72.5],
        [32.5, 74.5], [31.0, 75.5], [29.0, 76.0], [28.0, 75.5],
        [27.5, 76.5], [26.5, 75.5], [25.0, 74.5], [23.5, 72.5],
        [22.5, 70.0], [22.0, 68.5], [23.0, 66.0], [25.0, 63.0],
        [27.0, 61.5], [29.5, 60.5], [32.0, 60.0], [35.0, 60.0],
        [37.0, 60.0],
      ],
      markers: [
        { lat: 27.3243, lng: 68.1375, label: 'Mohenjo-daro — Great Bath', color: '#92400e' },
        { lat: 30.6289, lng: 72.8648, label: 'Harappa — First excavated city', color: '#92400e' },
        { lat: 23.8835, lng: 70.2048, label: 'Dholavira — Gujarat (India)', color: '#b45309' },
        { lat: 29.2816, lng: 76.5825, label: 'Rakhigarhi — Largest IVC site', color: '#b45309' },
        { lat: 31.8714, lng: 73.1010, label: 'Kot Diji — Pre-Harappan site', color: '#78350f' },
      ],
    },
  },

  // ── Rajasthan / Rajput ────────────────────────────────────────────────────
  {
    keywords: ['rajasthan', 'rajput', 'miniature painting', 'mewar', 'marwar', 'bundi', 'kishangarh', 'jaipur', 'udaipur'],
    text: `Rajput miniature painting encompasses a diverse family of regional schools that flourished across Rajasthan and the surrounding princely states between the 16th and 19th centuries, each with distinct palettes, subject matter, and stylistic conventions.\n\nThe Mewar school (Udaipur) is among the oldest, characterised by bold outlines, flat planes of vibrant colour, and crowded compositions depicting the Ramayana, Mahabharata, and Bhagavata Purana. The Bundi-Kota school is celebrated for lush forest settings, while the Kishangarh school — most famous for its elongated facial features and dreamy landscapes — reached its apogee under Nihal Chand's depictions of the romantic ideals of Radha and Krishna.\n\nRajput manuscripts and paintings were preserved in royal collections and temple treasuries, many of which now reside in the National Museum, the Maharaja Sawai Man Singh II Museum, and major collections abroad.`,
    citation: '7',
    source: 'Maharaja Sawai Man Singh II Museum — Rajput Paintings Archive',
    insightCard: {
      title: 'Maharana Jagat Singh II Hunting',
      period: 'c. 1750 · Mewar',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBAb5WAS4J9mFoReTf6lnYxUH8oQuf5w5TKYmMBjdT7KTVdtU4uHyJjj8l1X8mJfVxcdQhl1GjfSr6jiYp2vAW6XZjNxTcixJwVovpcwYh6WsCWxIk5wzc7QMLzZ0Vp6efyvtiHkhybxtOtkR1QpgZ0SX4iJ4EHM-lkI0q_XMxah71e3wkSBGqfXAS0uVjqORVyI-dpOjZPjKNqU23rJN3rxEYtTQIUZ8JYRrhYjsxWuQMqvRJH-ePJDegqdPIAxizQCmyRA9WvFA',
      link: '/artifact',
    },
    mapEvent: { pinId: 'rajasthan', label: 'Rajasthan' },
    geoData: {
      type: 'region',
      label: 'Rajputana Principalities (c. 18th Century)',
      color: '#b91c1c',
      center: [26.0, 74.0],
      zoom: 6,
      polygon: [
        [29.0, 70.0], [30.0, 74.0], [28.0, 77.0], [25.0, 78.0],
        [24.0, 76.0], [24.0, 72.0], [26.0, 69.5], [29.0, 70.0]
      ],
      markers: [
        { lat: 24.5854, lng: 73.7125, label: 'Udaipur — Mewar school', color: '#b91c1c' },
        { lat: 25.1462, lng: 75.8513, label: 'Bundi — Bundi-Kota school', color: '#dc2626' },
        { lat: 27.4008, lng: 70.9072, label: 'Kishangarh — Kishangarh school', color: '#ef4444' },
        { lat: 26.9124, lng: 75.7873, label: 'Jaipur — Amber Fort & Palace', color: '#b91c1c' },
        { lat: 26.2389, lng: 73.0243, label: 'Jodhpur — Mehrangarh Fort', color: '#991b1b' },
      ],
    },
  },

  // ── Hampi / Vijayanagara ──────────────────────────────────────────────────
  {
    keywords: ['hampi', 'vijayanagara', 'vijaynagar', 'karnataka', 'krishnadevaraya', 'vittala'],
    text: `Hampi, the ruined capital of the Vijayanagara Empire (1336–1646 CE), spreads across 4,100 hectares in the Bellary district of Karnataka. At its peak under Emperor Krishnadevaraya (r. 1509–1529), it was one of the world's largest cities with a population exceeding 500,000.\n\nThe empire was a Hindu kingdom that stood as the last great bulwark against the Deccan Sultanates. Its artists and architects created a distinctive style blending Chalukya, Hoysala, and Dravidian elements, producing the iconic Vittala Temple complex with its stone chariot and musical pillars — pillars that produce musical notes when struck.\n\nHampi was sacked and burned by a confederation of Deccan Sultanates following the Battle of Talikota (1565 CE). The ruins were inscribed as a UNESCO World Heritage Site in 1986. Over 1,600 monuments survive across its boulder-strewn landscape.`,
    citation: 'H-1',
    source: 'Karnataka Archaeological Department — Hampi Heritage Documentation',
    insightCard: {
      title: 'Vittala Temple Stone Chariot',
      period: '15th–16th Century CE · Vijayanagara',
      image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Hampi_Stone_Chariot.jpg/640px-Hampi_Stone_Chariot.jpg',
      link: '/artifact',
    },
    mapEvent: null,
    geoData: {
      type: 'region',
      label: 'Vijayanagara Empire Peak (c. 1520 CE)',
      color: '#b45309',
      center: [14.0, 77.0],
      zoom: 6,
      polygon: [
        [16.5, 73.5], [17.0, 78.5], [16.0, 81.5], [12.0, 80.0],
        [9.0, 78.5], [8.0, 77.0], [11.5, 75.0], [14.5, 74.0], [16.5, 73.5]
      ],
      markers: [
        { lat: 15.3350, lng: 76.4600, label: 'Hampi — Vijayanagara capital ruins', color: '#b45309' },
        { lat: 15.3349, lng: 76.4601, label: 'Virupaksha Temple — Active since 7th century', color: '#78350f' },
        { lat: 15.3265, lng: 76.4620, label: 'Lotus Mahal — Royal enclosure', color: '#b45309' },
      ],
    },
  },

  // ── Khajuraho ─────────────────────────────────────────────────────────────
  {
    keywords: ['khajuraho', 'chandela', 'erotic', 'kandariya', 'lakshmana temple'],
    text: `The Khajuraho temples (950–1050 CE) were built by the Chandela dynasty in Madhya Pradesh. Of the original 85 temples, 25 survive across three groups in Chhatarpur district — inscribed as a UNESCO World Heritage Site in 1986.\n\nThe temples are renowned for their erotic sculptures (mithuna), which adorn the exterior walls in bands. These constitute roughly 10% of the total sculptural program — the rest depicts gods, celestial beings, animals, and everyday life. The sculptures are variously interpreted as representations of tantric practice, a celebration of human life as a sacred act, or a symbolic boundary between the profane outer world and the sacred inner sanctum.\n\nThe Kandariya Mahadeva temple (c. 1030 CE) is the largest and most ornate, rising 30.5 metres and containing over 900 sculptures.`,
    citation: 'K-1',
    source: 'UNESCO World Heritage List — Khajuraho Group of Monuments',
    insightCard: {
      title: 'Kandariya Mahadeva Temple',
      period: 'c. 1030 CE · Chandela Dynasty',
      image: 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Kandariya_Mahadeva_Temple.jpg/640px-Kandariya_Mahadeva_Temple.jpg',
      link: '/artifact',
    },
    mapEvent: { pinId: 'mp' },
    geoData: {
      type: 'marker',
      lat: 24.8514,
      lng: 79.9211,
      label: 'Khajuraho Temples — Chandela Dynasty, Madhya Pradesh',
      zoom: 14,
    },
  },

  // ── Buddhism ──────────────────────────────────────────────────────────────
  {
    keywords: ['buddhism', 'buddhist', 'buddha', 'gandhara', 'stupa', 'sanchi', 'ajanta', 'ellora', 'bodh gaya'],
    text: `Buddhist art in the Indian subcontinent spans over two millennia and encompasses some of humanity's most transcendent artistic expressions.\n\nThe earliest Buddhist monuments — the stupas at Sanchi (3rd century BCE), with their elaborately carved gateways (toranas) — established an iconographic vocabulary that would spread across Asia. The Sanchi Stupa's toranas depict Jataka tales, the life of the Buddha, and yaksha and yakshini figures in deep relief.\n\nThe Gandhara school (1st–5th century CE, modern-day Pakistan and Afghanistan) produced the first anthropomorphic images of the Buddha, fusing Hellenistic artistic conventions with Buddhist iconography.\n\nAjanta Caves (Maharashtra) contain extraordinary narrative mural paintings from the 2nd century BCE to 6th century CE, preserved within 30 rock-cut cave monasteries and prayer halls.`,
    citation: '8',
    source: 'UNESCO World Heritage Committee — Buddhist Monuments at Sanchi',
    insightCard: {
      title: 'Standing Buddha',
      period: '2nd–3rd Century CE · Gandhara',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuD8WaUj_jVhKSH-JiGJA2c10JYbUHVMYJSgs5GV8niC6EyqC0apAWj2jVxyexeUA305BqMEbQZXyjdQBNocuT5YeCBs_xwOfrENQuyxNoYINX6qi-4k5vqM2oTCOVcKRmyk-UckiXjGaDSxL6xZnjtdqbVWoVMTEVZaq8tyXnBG57v40DZSMi33Kh7p64gCeFfI9UX0cNZK5j1PLb6uojnygN6rvfzFtNoTWkXoVL2tge9avQ3zD8Lu7bPvpzsA_oK5IVyWc7-vDg',
      link: '/artifact',
    },
    mapEvent: null,
    geoData: {
      type: 'markers',
      center: [23.0, 80.0],
      zoom: 5,
      points: [
        { lat: 23.4820, lng: 77.7378, label: 'Sanchi — Great Stupa', color: '#b45309' },
        { lat: 24.7971, lng: 84.9984, label: 'Bodh Gaya — Enlightenment site', color: '#92400e' },
        { lat: 20.5519, lng: 75.7033, label: 'Ajanta Caves — Murals & rock-cut art', color: '#b45309' },
        { lat: 20.0258, lng: 75.1780, label: 'Ellora Caves — Buddhist, Hindu & Jain', color: '#78350f' },
        { lat: 25.3754, lng: 82.9876, label: 'Sarnath — First sermon of the Buddha', color: '#b45309' },
      ],
    },
  },

  // ── Textiles ──────────────────────────────────────────────────────────────
  {
    keywords: ['textile', 'silk', 'weaving', 'kanchipuram', 'banarasi', 'ikat', 'kalamkari', 'batik', 'zari'],
    text: `India's textile traditions rank among the most sophisticated and geographically diverse in the world, developed over thousands of years of craftsmanship.\n\nKanchipuram silk (Tamil Nadu) is renowned for its heavyweight pure silk with contrasting borders and end-pieces woven separately and attached. The zari work — fine gold or silver thread woven into the fabric — creates temple motifs, checks, and stripes that have been coveted for centuries.\n\nBanarasi brocades from Varanasi incorporate real gold and silver threads (zari), producing luxuriant fabrics with Mughal-inspired floral and arabesque motifs. Kalamkari (Andhra Pradesh) uses natural dyes applied by pen (kalam) or block to cotton, depicting mythological scenes.\n\nIkat weaving, practised in Odisha (Sambalpuri), Gujarat (Patola), and Andhra Pradesh (Pochampally), creates patterns through resist-dyeing of threads before weaving — a technically demanding process that produces characteristic blurred-edge designs.`,
    citation: '9',
    source: 'Craft Documentation Society of India — Textile Heritage Atlas',
    insightCard: {
      title: 'Kanchipuram Silk',
      period: '18th Century · Tamil Nadu',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCyMtcK8zGEONNPUhqjTz8tIuURSuAZgFayydOv_zIQZERb4qKfguIpALpJLnmZEt-BYyOvCJGM_DW5X1J47bg8rjnM9Ph48-CKXMxH-F4Ij4ix4Y3c1bGjuYeNuX7YDdI_oYk3mhPRKtkI2BFOfBuIFAaLpJJSPasUYGOVrfbLqNDHxQNlB3SaJ1Sj5361zmS8b5hUD-94z5GwmUY15HIyUPZwE6AWvSP54rQ-8zp5ZhQ9rlJsNAXxUP9s9QyurCiVgAuzQdychQoA',
      link: '/artifact',
    },
    mapEvent: { pinId: 'tn', label: 'Tamil Nadu' },
    geoData: {
      type: 'markers',
      center: [17.0, 79.0],
      zoom: 6,
      points: [
        { lat: 12.8342, lng: 79.7036, label: 'Kanchipuram — Kanjivaram silk', color: '#7b1fa2' },
        { lat: 25.3176, lng: 82.9739, label: 'Varanasi — Banarasi brocades', color: '#6a0dad' },
        { lat: 14.4673, lng: 79.9952, label: 'Srikalahasti — Kalamkari art', color: '#9c27b0' },
        { lat: 21.4669, lng: 83.9812, label: 'Sambalpur — Sambalpuri ikat', color: '#ab47bc' },
        { lat: 16.9944, lng: 79.3732, label: 'Pochampally — Pochampalli ikat', color: '#8e24aa' },
      ],
    },
  },

  // ── Fallback ──────────────────────────────────────────────────────────────
  {
    keywords: [],
    text: `India's cultural heritage spans over five millennia and encompasses an extraordinary breadth of artistic traditions — from the enigmatic seals of the Indus Valley Civilisation to the living folk arts practised by tribal communities today.\n\nThe Arkana archive holds records of over 1,200 artefacts across categories including sculpture, painting, manuscript, textile, metalwork, and architecture. You can explore specific traditions such as Warli art, Gond painting, Mughal miniatures, Chola bronzes, or Rajput manuscripts — or ask about particular artefacts, dynasties, regions, or time periods.\n\nWhat aspect of India's heritage would you like to explore?`,
    citation: null,
    source: null,
    insightCard: null,
    mapEvent: null,
    geoData: null,
  },
];

/**
 * Find the best matching response for a given user query.
 * Scores by keyword hit count; returns the highest-scoring entry.
 * Falls back to the last entry (fallback) if no keywords match.
 */
export function findResponse(query) {
  const lowerQuery = query.toLowerCase();
  let bestMatch = DEMO_KNOWLEDGE_BASE[DEMO_KNOWLEDGE_BASE.length - 1];
  let bestScore = 0;

  for (const entry of DEMO_KNOWLEDGE_BASE.slice(0, -1)) {
    let score = 0;
    for (const kw of entry.keywords) {
      if (lowerQuery.includes(kw)) score += kw.split(' ').length; // longer phrases score higher
    }
    if (score > bestScore) {
      bestScore = score;
      bestMatch = entry;
    }
  }
  return bestMatch;
}
