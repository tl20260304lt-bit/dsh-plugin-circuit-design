#!/usr/bin/env python3
"""PDN (Power Delivery Network) Impedance Analysis.

Calculate target impedance and verify decoupling capacitor coverage.
Usage: python pdn_analysis.py --voltage 0.85 --current 12 --delta-v 2 --inductance 5e-12
"""
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def calculate_target_impedance(voltage, current, delta_v_percent):
    """Calculate Z_target = V * (delta_v/100) / I."""
    return voltage * (delta_v_percent / 100) / current


def capacitor_impedance(f, c, esr, esl):
    """Capacitor impedance across frequency."""
    z_c = 1.0 / (2 * np.pi * 1j * f * c)
    z_l = 2 * np.pi * 1j * f * esl
    return z_c + esr + z_l


def parallel_impedance(z_list):
    """Parallel combination of impedances."""
    return 1.0 / sum(1.0 / z for z in z_list)


def analyze_pdn(voltage, current, delta_v, inductance, capacitors, f_min=1e3, f_max=1e9, points=1000):
    """Full PDN analysis.

    Args:
        voltage: Supply voltage in Volts
        current: Load current in Amps
        delta_v: Allowed ripple as percentage (e.g., 2 for 2%)
        inductance: Plane inductance in Henrys (typically 1-10 pH per square)
        capacitors: List of dicts with keys: C (Farads), ESR (Ohms), ESL (Henrys), count (int)
        f_min: Minimum frequency in Hz
        f_max: Maximum frequency in Hz
        points: Number of frequency points

    Returns:
        dict with frequency, impedance, and pass/fail status
    """
    f = np.logspace(np.log10(f_min), np.log10(f_max), points)
    z_target = calculate_target_impedance(voltage, current, delta_v)

    # Plane inductance impedance
    z_plane = 2 * np.pi * 1j * f * inductance

    # Capacitor network
    z_caps = []
    for cap in capacitors:
        z_single = capacitor_impedance(f, cap['C'], cap['ESR'], cap['ESL'])
        # Parallel count
        z_parallel = z_single / cap['count']
        z_caps.append(z_parallel)

    # Total PDN impedance
    z_total_list = [z_plane] + z_caps
    z_pdn = parallel_impedance(z_total_list)
    z_mag = np.abs(z_pdn)

    # Check pass/fail
    pass_ratio = np.mean(z_mag < z_target)

    return {
        'frequency': f.tolist(),
        'impedance': z_mag.tolist(),
        'z_target': z_target,
        'pass_ratio': float(pass_ratio),
        'pass': pass_ratio > 0.9  # 90% of bandwidth below target
    }


def generate_plot(result, output='pdn_analysis.png'):
    """Generate PDN impedance plot."""
    f = np.array(result['frequency'])
    z = np.array(result['impedance'])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogx(f, z * 1000, 'b-', linewidth=1.5, label='PDN Impedance')
    ax.axhline(y=result['z_target'] * 1000, color='r', linestyle='--', label=f"Z_target = {result['z_target']*1000:.2f} mΩ")
    ax.fill_between(f, 0, result['z_target'] * 1000, alpha=0.1, color='green', label='Pass Region')

    ax.set_xlabel('Frequency (Hz)', fontsize=12)
    ax.set_ylabel('Impedance (mΩ)', fontsize=12)
    ax.set_title('PDN Impedance Analysis', fontsize=14)
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(loc='best')

    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()
    return output


def main():
    parser = argparse.ArgumentParser(description='PDN Impedance Analysis')
    parser.add_argument('--voltage', type=float, required=True, help='Supply voltage (V)')
    parser.add_argument('--current', type=float, required=True, help='Load current (A)')
    parser.add_argument('--delta-v', type=float, default=2.0, help='Allowed ripple percentage')
    parser.add_argument('--inductance', type=float, default=5e-12, help='Plane inductance (H), default 5pH/sq')
    parser.add_argument('--capacitors', type=str, default=None,
                        help='JSON string of capacitor list: [{"C": 10e-6, "ESR": 0.01, "ESL": 1e-9, "count": 10}, ...]')
    parser.add_argument('--output', type=str, default='pdn_analysis_results.json', help='Output JSON file')
    parser.add_argument('--plot', type=str, default='pdn_analysis.png', help='Output plot file')

    args = parser.parse_args()

    # Default capacitor network if not specified
    if args.capacitors:
        capacitors = json.loads(args.capacitors)
    else:
        # Typical decoupling network
        capacitors = [
            {'C': 10e-6, 'ESR': 0.02, 'ESL': 3e-9, 'count': 10},  # 10µF bulk
            {'C': 0.1e-6, 'ESR': 0.05, 'ESL': 1e-9, 'count': 20},  # 0.1µF mid
            {'C': 0.01e-6, 'ESR': 0.1, 'ESL': 0.3e-9, 'count': 40},  # 0.01µF high-freq
        ]

    result = analyze_pdn(
        voltage=args.voltage,
        current=args.current,
        delta_v=args.delta_v,
        inductance=args.inductance,
        capacitors=capacitors
    )

    # Save results
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    # Generate plot
    plot_file = generate_plot(result, args.plot)

    print(f"Z_target: {result['z_target']*1000:.2f} mΩ")
    print(f"Pass ratio: {result['pass_ratio']*100:.1f}%")
    print(f"Status: {'✅ PASS' if result['pass'] else '❌ FAIL'}")
    print(f"Results saved to: {args.output}")
    print(f"Plot saved to: {plot_file}")


if __name__ == '__main__':
    main()