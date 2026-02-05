/**
 * Chat emoji configuration for message input
 * Organized by category for better UX
 */

type EmojiDef = {
  symbol: string;
  label: string;
  shortcode: string;
};

class ChatEmojiRegistry {
  private positiveEmojis: Map<string, EmojiDef> = new Map();
  private actionEmojis: Map<string, EmojiDef> = new Map();
  private shortcodeLookup: Map<string, string> = new Map();

  constructor() {
    this.initializePositiveEmojis();
    this.initializeActionEmojis();
    this.buildShortcodeLookup();
  }

  private initializePositiveEmojis() {
    // Sunshine emoji - primary addition for this feature
    this.positiveEmojis.set('sun', {
      symbol: '☀️',
      label: 'Sunshine',
      shortcode: ':sun:'
    });
    
    this.positiveEmojis.set('grin', {
      symbol: '😊',
      label: 'Smiling Face',
      shortcode: ':grin:'
    });
    
    this.positiveEmojis.set('love', {
      symbol: '❤️',
      label: 'Red Heart',
      shortcode: ':love:'
    });
    
    this.positiveEmojis.set('sparkle', {
      symbol: '⭐',
      label: 'Star',
      shortcode: ':sparkle:'
    });
  }

  private initializeActionEmojis() {
    this.actionEmojis.set('approve', {
      symbol: '👍',
      label: 'Thumbs Up',
      shortcode: ':approve:'
    });
    
    this.actionEmojis.set('launch', {
      symbol: '🚀',
      label: 'Rocket',
      shortcode: ':launch:'
    });
    
    this.actionEmojis.set('hot', {
      symbol: '🔥',
      label: 'Fire',
      shortcode: ':hot:'
    });
    
    this.actionEmojis.set('confirmed', {
      symbol: '✅',
      label: 'Check Mark Button',
      shortcode: ':confirmed:'
    });
  }

  private buildShortcodeLookup() {
    // Preprocess shortcodes for faster lookup
    this.positiveEmojis.forEach((def) => {
      const normalized = def.shortcode.toLowerCase().replace(/:/g, '');
      this.shortcodeLookup.set(normalized, def.symbol);
    });
    
    this.actionEmojis.forEach((def) => {
      const normalized = def.shortcode.toLowerCase().replace(/:/g, '');
      this.shortcodeLookup.set(normalized, def.symbol);
    });
  }

  getAllForPicker(): Array<EmojiDef & { category: string; key: string }> {
    const results: Array<EmojiDef & { category: string; key: string }> = [];
    
    this.positiveEmojis.forEach((def, key) => {
      results.push({ ...def, category: 'positive', key });
    });
    
    this.actionEmojis.forEach((def, key) => {
      results.push({ ...def, category: 'action', key });
    });
    
    return results;
  }

  findByShortcode(code: string): string | null {
    const normalized = code.toLowerCase().replace(/:/g, '');
    return this.shortcodeLookup.get(normalized) || null;
  }
}

export const chatEmojiRegistry = new ChatEmojiRegistry();
