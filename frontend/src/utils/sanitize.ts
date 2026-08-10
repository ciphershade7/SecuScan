import DOMPurify from 'dompurify'

/**
 * Aggressive, paranoid sanitization for all untrusted scanner output.
 * Strips all HTML tags and ensures strict neutralization of malicious payloads.
 */
export const sanitizeRawOutput = (input: string | unknown): string => {
    if (input === null || input === undefined) return ''
    const strInput = String(input)
    
    // We want to strip all HTML tags entirely since raw scanner output shouldn't render as HTML
    return DOMPurify.sanitize(strInput, {
        ALLOWED_TAGS: [], // No tags allowed
        ALLOWED_ATTR: [], // No attributes allowed
        KEEP_CONTENT: true, // Keep the text content inside tags if they are stripped
    })
}
