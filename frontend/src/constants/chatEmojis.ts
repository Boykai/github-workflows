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

  constructor() {
    this.initializePositiveEmojis();
    this.initializeActionEmojis();
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
    
    for (const [, def] of this.positiveEmojis) {
      if (def.shortcode.replace(/:/g, '') === normalized) {
        return def.symbol;
      }
    }
    
    for (const [, def] of this.actionEmojis) {
      if (def.shortcode.replace(/:/g, '') === normalized) {
        return def.symbol;
      }
    }
    
    return null;
  }
}

export const chatEmojiRegistry = new ChatEmojiRegistry();
