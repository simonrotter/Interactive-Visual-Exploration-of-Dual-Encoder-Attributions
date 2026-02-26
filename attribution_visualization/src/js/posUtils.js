export function getPOSDisplayName(cat) {
    return categoryDisplayNames[cat] || cat
  }

  const categoryDisplayNames = {
  //POS tags
  ADJ: 'Adjective',
  ADP: 'Preposition',
  ADV: 'Adverb',
  AUX: 'Auxiliary verb',
  CONJ: 'Conjunction',
  CCONJ: 'Coordinating conjunction',
  DET: 'Determiner / Article',
  INTJ: 'Interjection',
  NOUN: 'Noun',
  NUM: 'Number',
  PART: 'Particle',
  PRON: 'Pronoun',
  PROPN: 'Proper noun',
  PUNCT: 'Punctuation',
  SCONJ: 'Subordinating conjunction',
  SYM: 'Symbol',
  VERB: 'Verb',
  X: 'Unknown',

  //NER stuff
  PERSON: 'Person',
  NORP: 'Nationality / Religious group / Political group',
  FAC: 'Facility / Infrastructure',
  ORG: 'Organization',
  GPE: 'Country / City / State',
  LOC: 'Location',
  PRODUCT: 'Product',
  EVENT: 'Event',
  WORK_OF_ART: 'Work of art',
  LAW: 'Law',
  LANGUAGE: 'Language',
  DATE: 'Date',
  TIME: 'Time',
  PERCENT: 'Percent',
  MONEY: 'Money',
  QUANTITY: 'Quantity',
  ORDINAL: 'Ordinal number',
  CARDINAL: 'Cardinal number',
}
