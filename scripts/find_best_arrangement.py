from math import sqrt, ceil

def find_best_arrangement(N):
    best_wasted_space = float('inf')
    best_width = 1
    best_height = N

    for width in range(1, ceil(sqrt(N)) + 1):
        height = (N + width - 1) // width  # Round up the division
        wasted_space = (width * height) - N

        if wasted_space < best_wasted_space or (wasted_space == best_wasted_space and abs(width - height) < abs(best_width - best_height)):
                best_wasted_space = wasted_space
                best_width = width
                best_height = height

    return best_width, best_height

if __name__ == "__main__":

    import sys

    # Example usage:
    N = sys.argv[1]
    width, height = find_best_arrangement(int(N))
    print(f"Best arrangement for {N} elements: {width} x {height}")

    # row = ' '.join("o " for _ in range(width))
    # for r in range(height):
    #     print(row)
