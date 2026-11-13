/*
 * Sprite resolution deliberately lives outside app.js.
 * A missing shiny/variant image must never silently become a different form
 * or a non-shiny sprite. No image files are stored in SQLite.
 *
 * Sources: PokeAPI/sprites (pixel sprites, HOME 3D renders),
 *          Pokémon Showdown (form-specific stills and animated battle sprites).
 * The browser ONLY requests images via the local FastAPI disk cache; it never
 * contacts external hosts directly. Cache location: ~/.optpoke/sprites/.
 */
'use strict';
(function (root) {
  const POKE = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon';
  const SHOWDOWN = 'https://play.pokemonshowdown.com/sprites';
  const localImageURL = url => `/api/sprites/image?url=${encodeURIComponent(url)}`;

  const slug = (value) => String(value || '').toLowerCase()
    .replace(/♀/g, 'f').replace(/♂/g, 'm')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]/g, '');
  const baseForm = form => !form || ['original', 'normal', 'basic'].includes(form.toLowerCase());

  // Showdown uses a few form identifiers that differ from AustinJohn's labels.
  // Match by species AND form: an alias for one Pokémon must not affect another.
  function showdownForm(species, form) {
    const pokemon = slug(species);
    const value = String(form || '').toLowerCase().trim();
    const compact = slug(form);
    if (baseForm(form)) return pokemon;
    if (pokemon === 'unown') return `${pokemon}-${value === '!' ? 'exclamation' : value === '?' ? 'question' : compact || 'a'}`;
    if (pokemon === 'zygarde') return value === '0.5' ? pokemon : value === '0.1' ? 'zygarde-10' : null;
    if (pokemon === 'maushold') return value === 'family of 3' ? pokemon : value === 'family of 4' ? 'maushold-four' : null;
    if (pokemon === 'tauros') {
      const breed = /combat/.test(value) ? 'combat' : /blaze/.test(value) ? 'blaze' : /aqua/.test(value) ? 'aqua' : null;
      return breed ? `${pokemon}-paldea${breed}` : null;
    }
    if (pokemon === 'alcremie') {
      // Detailed sweet mapping is handled by alcremieSources() below.
      return null;
    }
    if (pokemon === 'gimmighoul') return /chest/i.test(form) ? pokemon : /roaming/i.test(form) ? 'gimmighoul-roaming' : null;
    if (pokemon === 'vivillon') return `${pokemon}-${compact}`;
    if (pokemon === 'pikachu' && value.endsWith(' cap')) return `${pokemon}-${slug(value.replace(/ cap$/, ''))}`;
    if (pokemon === 'magearna' && /original/i.test(form)) return 'magearna-original';
    if (pokemon === 'urshifu') return /single/i.test(form) ? pokemon : /rapid/i.test(form) ? 'urshifu-rapidstrike' : null;
    if (pokemon === 'minior') return `${pokemon}-${slug(value.replace(/ core$/, ''))}`;
    if (pokemon === 'oricorio') return `${pokemon}-${slug(value.replace(/ style$/, ''))}`;
    if (pokemon === 'pumpkaboo' || pokemon === 'gourgeist') {
      return /average/i.test(form) ? pokemon : `${pokemon}-${compact}`;
    }
    if (pokemon === 'tornadus' || pokemon === 'thundurus' || pokemon === 'landorus' || pokemon === 'enamorus') {
      return /incarnate/i.test(form) ? pokemon : /therian/i.test(form) ? `${pokemon}-therian` : null;
    }
    if (pokemon === 'deoxys') return `${pokemon}-${compact}`;
    if (pokemon === 'burmy' || pokemon === 'wormadam') return /plant/i.test(form) ? pokemon : `${pokemon}-${compact}`;
    if (pokemon === 'sinistea' || pokemon === 'polteageist') return /phony/i.test(form) ? pokemon : `${pokemon}-antique`;
    if (pokemon === 'poltchageist') return /counterfeit/i.test(form) ? pokemon : `${pokemon}-artisan`;
    if (pokemon === 'sinistcha') return /unremarkable/i.test(form) ? pokemon : `${pokemon}-masterpiece`;
    if (pokemon === 'dudunsparce') return /2 segment/i.test(form) ? pokemon : 'dudunsparce-three';
    if (pokemon === 'tatsugiri') return /curly/i.test(form) ? pokemon : `${pokemon}-${compact}`;
    if (pokemon === 'basculin') return /red/i.test(form) ? pokemon : `${pokemon}-${compact.replace('stripe','striped')}`;
    if (pokemon === 'toxtricity') return /amped/i.test(form) ? pokemon : 'toxtricity-lowkey';
    if (pokemon === 'shellos' || pokemon === 'gastrodon') return /west/i.test(form) ? pokemon : `${pokemon}-east`;
    if (pokemon === 'flabebe' || pokemon === 'floette' || pokemon === 'florges') {
      return /red/i.test(form) ? pokemon : `${pokemon}-${slug(value.replace(/ flower$/, ''))}`;
    }
    if (pokemon === 'squawkabilly') return /green/i.test(form) ? pokemon : `${pokemon}-${compact}`;
    if (pokemon === 'deerling' || pokemon === 'sawsbuck') return /spring/i.test(form) ? pokemon : `${pokemon}-${compact}`;
    if (pokemon === 'lycanroc') return /midday/i.test(form) ? pokemon : `${pokemon}-${compact}`;
    if (pokemon === 'zarude') return /dada/i.test(form) ? `${pokemon}-dada` : pokemon;
    if (pokemon === 'hoopa') return /unbound/i.test(form) ? `${pokemon}-unbound` : pokemon;
    if (/^alolan$|^galarian$|^hisuian$|^paldean$/.test(value)) {
      const region = {alolan:'alola',galarian:'galar',hisuian:'hisui',paldean:'paldea'}[value];
      return `${pokemon}-${region}`;
    }
    return `${pokemon}-${compact}`;
  }

  function alcremieSources(form, shiny) {
    const [cream, sweet = 'Strawberry'] = String(form).split(',').map(s => s.trim());
    if (!cream || !/cream|swirl/i.test(cream)) return [];
    const flavor = slug(cream);
    // Showdown's animated renders include the decoration (63 different looks).
    // 'Strawberry' is the default, so first try the unqualified form name.
    const sweetSlug = slug(sweet);
    const filename = sweetSlug === 'strawberry' ? (flavor === 'vanillacream' ? 'alcremie' : `alcremie-${flavor}`) : `alcremie-${flavor}-${sweetSlug}`;
    const animation = shiny ? 'ani-shiny' : 'ani';
    const still = shiny ? 'dex-shiny' : 'dex';
    const candidates = [`${SHOWDOWN}/${animation}/${filename}.gif`];
    if (sweetSlug !== 'strawberry') {
      // Historical naming convention for some older animated sweet renders.
      candidates.push(`${SHOWDOWN}/${animation}/alcremie-${slug(cream).replace(/cream$/, '-cream').replace(/swirl$/, '-swirl')}-${sweetSlug}.gif`);
    }
    // Static render can show cream color but not the correct sweet. Do not use it.
    return candidates.map(url => ({url, kind:'render'}));
  }

  function spriteSources(item, shiny) {
    const id = Number(item.dex_number);
    const sources = [];
    const add = (url, kind) => {
      if (!sources.some(s => s.url === url)) sources.push({url,kind});
    };
    if (!Number.isInteger(id) || id < 1) return sources;
    const standard = baseForm(item.form_name);
    const suffix = shiny ? '/shiny' : '';
    if (standard) {
      add(`${POKE}${suffix}/${id}.png`, 'pixel');
      add(`${POKE}/other/home${suffix}/${id}.png`, 'render');
      add(`${POKE}/other/official-artwork${suffix}/${id}.png`, 'render');
      // Other sprite sources have broader coverage of recent generations.
      add(`${SHOWDOWN}/${shiny ? 'dex-shiny' : 'dex'}/${slug(item.species)}.png`, 'pixel');
      return sources;
    }
    if (slug(item.species) === 'alcremie') return alcremieSources(item.form_name, shiny);

    const variant = showdownForm(item.species, item.form_name);
    if (variant) {
      add(`${SHOWDOWN}/${shiny ? 'dex-shiny' : 'dex'}/${variant}.png`, 'pixel');
      add(`${SHOWDOWN}/${shiny ? 'ani-shiny' : 'ani'}/${variant}.gif`, 'render');
    }
    // For forms without images in Showdown, PokeAPI's variety API can provide
    // a form-specific HOME render. See loadSprite() below.
    return sources;
  }

  const varietyCache = new Map();
  function pokeApiVariety(item) {
    const pokemon = slug(item.species);
    const value = String(item.form_name || '').toLowerCase();
    if (/^alolan$|^galarian$|^hisuian$|^paldean$/.test(value)) {
      return `${pokemon}-${{alolan:'alola',galarian:'galar',hisuian:'hisui',paldean:'paldea'}[value]}`;
    }
    // PokeAPI has additional varieties with these identifiers.
    const supported = {
      deoxys: {Attack:'attack',Defense:'defense',Speed:'speed'},
      rotom: {Heat:'heat',Wash:'wash',Frost:'frost',Fan:'fan',Mow:'mow'},
      giratina: {Origin:'origin'},
      shaymin: {Sky:'sky'},
      tornadus:{Therian:'therian'},thundurus:{Therian:'therian'},
      landorus:{Therian:'therian'},enamorus:{Therian:'therian'},
      hoopa:{Unbound:'unbound'},
    };
    const form = supported[pokemon]?.[item.form_name];
    return form ? `${pokemon}-${form}` : null;
  }
  async function fetchVarietyRender(item, shiny) {
    const key = pokeApiVariety(item);
    if (!key) return null;
    if (!varietyCache.has(key)) {
      varietyCache.set(key, (async () => {
        try {
          const response = await fetch(`/api/sprites/variety/${encodeURIComponent(key)}`, {signal:AbortSignal.timeout(5000)});
          if (!response.ok) return null;
          return (await response.json()) || null;
        } catch { return null; }
      })());
    }
    const sprites = await varietyCache.get(key);
    if (!sprites) return null;
    // Important: never use front_default for a requested shiny.
    return shiny ? (sprites.shiny || null) : (sprites.normal || null);
  }

  function loadSprite(image, item, shiny) {
    const placeholder = image.nextElementSibling;
    const candidates = spriteSources(item, shiny);
    let index = 0;
    let fallbackLookup = false;
    let current = null;
    const next = async () => {
      if (!image.isConnected) return; // Cards may have been replaced by a filter/search.
      if (index < candidates.length) {
        current = candidates[index++];
        image.src = localImageURL(current.url);
      } else if (!fallbackLookup) {
        fallbackLookup = true;
        const render = await fetchVarietyRender(item, shiny);
        if (render && image.isConnected) {
          current = {url:render,kind:'render'};
          image.src = localImageURL(render);
        } else if (image.isConnected) showPlaceholder();
      } else {
        showPlaceholder();
      }
    };
    const showPlaceholder = () => {
      image.style.display = 'none';
      if (placeholder) placeholder.style.display = 'grid';
    };
    image.addEventListener('load', () => {
      image.classList.toggle('sprite-render', current?.kind === 'render');
      image.style.display = '';
      if (placeholder) placeholder.style.display = 'none';
    });
    image.addEventListener('error', next);
    next();
  }

  const api = {spriteSources, showdownForm, loadSprite, pokeApiVariety, localImageURL};
  root.OptPokeSprites = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
