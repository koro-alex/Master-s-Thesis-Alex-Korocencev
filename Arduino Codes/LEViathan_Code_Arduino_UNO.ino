#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/power.h>
#include <avr/pgmspace.h>

#define N_DIVS 24

// --- State Variables ---
static uint8_t ofsZT = 0, ofsAD = 0, ofsWS = 0;
static uint8_t invM = 0, invB = 0, invN = 0;

static uint8_t tableD[N_DIVS], tableB[N_DIVS], tableC[N_DIVS];

const uint8_t baseWave[24] PROGMEM = {
  1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0
};

#define MASK_D 0b11111100
#define MASK_B 0b00110011
#define MASK_C 0b00111111

void uart_init() {
  UBRR0H = 0;
  UBRR0L = 16; // 115200 baud
  UCSR0A = _BV(U2X0);
  UCSR0B = _BV(RXEN0) | _BV(TXEN0);
  UCSR0C = _BV(UCSZ01) | _BV(UCSZ00);
}

uint8_t get_state(uint8_t step, uint8_t ofs, uint8_t inv) {
  return (pgm_read_byte(&baseWave[(step + ofs) % 24]) ^ inv);
}

void rebuild_tables() {
  for (uint8_t s = 0; s < N_DIVS; ++s) {
    uint8_t d = 0, b = 0, c = 0;
    uint8_t m1 = (ofsAD + ofsWS) % 24, m2 = ofsWS, m3 = ofsAD, m4 = 0;

    if (get_state(s, m1 + ofsZT, invM ^ invB ^ invN)) d |= (1<<PD2); else d |= (1<<PD3);
    if (get_state(s, m1, invB ^ invN))               d |= (1<<PD4); else d |= (1<<PD5);
    if (get_state(s, m2 + ofsZT, invM ^ invN))        d |= (1<<PD6); else d |= (1<<PD7);
    if (get_state(s, m2, invN))                      b |= (1<<PB0); else b |= (1<<PB1);
    if (get_state(s, m3 + ofsZT, invM ^ invB))        b |= (1<<PB4); else b |= (1<<PB5);
    if (get_state(s, m3, invB))                      c |= (1<<PC0); else c |= (1<<PC1);
    if (get_state(s, m4 + ofsZT, invM))               c |= (1<<PC2); else c |= (1<<PC3);
    if (get_state(s, m4, 0))                         c |= (1<<PC4); else c |= (1<<PC5);

    tableD[s] = d; tableB[s] = b; tableC[s] = c;
  }
}

// --- Precise Timing Macro ---
// Each FIRE now takes ~16 cycles. 
// 16 cycles * 24 steps = 384 cycles.
// This leaves only 16 cycles of "gap", making the transition almost invisible.
#define FIRE(n) \
  PORTD = tableD[n]; PORTB = tableB[n]; PORTC = tableC[n]; \
  __asm__ __volatile__ ("nop\nnop\nnop\nnop\nnop\nnop\nnop\n");

void setup() {
  DDRD |= MASK_D; DDRB |= MASK_B; DDRC |= MASK_C;
  DDRB &= ~(1 << PB3); PORTB |= (1 << PB3); 
  
  cli();
  TCCR1A = _BV(WGM10) | _BV(WGM11) | _BV(COM1B1);
  TCCR1B = _BV(WGM12) | _BV(WGM13) | _BV(CS10);
  OCR1A = 399; OCR1B = 200; 
  DDRB |= (1 << PB2);
  sei();

  power_adc_disable(); power_spi_disable(); power_twi_disable(); power_timer0_disable();
  uart_init();
  rebuild_tables();

  cli(); 

  while (1) {
    // 1. Check UART for commands
    if (UCSR0A & _BV(RXC0)) {
      uint8_t ch = UDR0;
      uint8_t changed = 1;
      if (ch == 't') ofsZT = (ofsZT + 1) % 24; 
      else if (ch == 'z') ofsZT = (ofsZT + 23) % 24;
      else if (ch == 'a') ofsAD = (ofsAD + 1) % 24; 
      else if (ch == 'd') ofsAD = (ofsAD + 23) % 24;
      else if (ch == 'w') ofsWS = (ofsWS + 1) % 24; 
      else if (ch == 's') ofsWS = (ofsWS + 23) % 24;
      else if (ch == 'm') invM = !invM; 
      else if (ch == 'b') invB = !invB; 
      else if (ch == 'n') invN = !invN;
      else if (ch == 'o') { ofsZT=0; ofsAD=0; ofsWS=0; invM=0; invB=0; invN=0; }
      else { changed = 0; }
      
      if (changed) rebuild_tables();
    }

    // 2. Wait for Sync Low (Start of 40kHz cycle)
    while (PINB & 0b00001000); 

    // 3. High-Precision Pulse Train
    FIRE(0) FIRE(1) FIRE(2) FIRE(3) FIRE(4) FIRE(5)
    FIRE(6) FIRE(7) FIRE(8) FIRE(9) FIRE(10) FIRE(11)
    FIRE(12) FIRE(13) FIRE(14) FIRE(15) FIRE(16) FIRE(17)
    FIRE(18) FIRE(19) FIRE(20) FIRE(21) FIRE(22) FIRE(23)

    // 4. Wait for Sync High (End of 40kHz cycle)
    while (!(PINB & 0b00001000)); 
  }
}
void loop() {}
