const dictionaries = {};

let currentLanguage = "en";

export const i18n = {
  async load(language) {
    currentLanguage = language;
    const response = await fetch(`./src/i18n/${language}.json`);
    dictionaries[language] = await response.json();
  },

  currentLanguage() {
    return currentLanguage;
  }
};

export function t(key) {
  const dictionary = dictionaries[currentLanguage] ?? {};
  return key.split(".").reduce((node, part) => node?.[part], dictionary) ?? key;
}
