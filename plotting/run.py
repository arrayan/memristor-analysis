from plotting.config import load_config
from plotting.pipeline import load_all
from plotting.fig_characteristic import build_characteristic_fig


def main() -> None:
    cfg = load_config()
    data = load_all(cfg)

    fig = build_characteristic_fig(data.raw_characteristic, data.sets)
    out = cfg.output_dir / cfg.characteristic_html
    fig.write_html(out)
    print("Wrote:", out)


if __name__ == "__main__":
    main()
