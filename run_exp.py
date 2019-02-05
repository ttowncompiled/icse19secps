from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import pandas as pd
import random
import seaborn as sns

def run_trial(alpha, beta, n, uav_conf, victim_conf, adj, turns, collisions=False, stay_put=False):
    """
        Executes a single trial of the experiment with the provided parameters.

        INPUT:
            alpha - The probability that a victim remains in their current zone for the next turn,
            beta - The probability that the UAV's sensors detect a victim in the same zone,
            n - The number of zones in the city,
            uav_conf - A list of indices representing the locations of the UAVs,
            victim_conf - A list of indices representing the locations of the victims,
            adj - A dictionary which takes a zone i and returns the zones adjacent to i,
            turns - The number of turns to run the trial,
            collisions - Whether collisions should be minimized or ignored, and
            stay_put - Whether half the UAVs should remain at their initial location or all move.
        OUTPUT:
            A list of triples (alpha, beta, accrued-reward).
    """
    heatmap, reward = [ 1.0 / float(n) for _ in range(n) ], 0.0
    for t in range(turns):
        # system player turn
        sys_turn = []
        idx = 0
        for u_zone in uav_conf:
            next_zone = u_zone
            # update location of UAV
            if not stay_put or idx % 2 == 0:
                for a_j in adj[u_zone]:
                    if heatmap[a_j] > heatmap[next_zone]:
                        if a_j in sys_turn and collisions:
                            continue
                        next_zone = a_j
            sys_turn.append(next_zone)
            idx += 1
        uav_conf = sys_turn
        for next_zone in uav_conf:
            # update heatmap after performing a scan
            heatmap[next_zone] = heatmap[next_zone] * (1 - beta)
        # update accrued reward
        reward = 1 - sum(heatmap)
        # environmental player turn
        env_turn = []
        for v_zone in victim_conf:
            thwart = True
            for u_zone in uav_conf:
                if u_zone == v_zone:
                    # attempt to thwart scan
                    if random.uniform(0, 1) <= beta:
                        thwart = False
            if not thwart:
                continue
            next_zone = v_zone
            # attempt to move the victim
            if random.uniform(0, 1) > alpha:
                next_zone = random.choice(adj[v_zone])
            env_turn.append(next_zone)
        victim_conf = env_turn
        # update the heatmap to account for the potential moves
        for i in range(n):
            heatmap[i] = heatmap[i] * alpha
            for j in adj[i]:
                heatmap[i] += heatmap[j] * (1 - alpha) * 1.0 / len(adj[j])
    return (alpha, beta, reward)


def run_trials(uav_count, victim_count, n, rows, cols, adj, alphas, betas, t, state):
    r1, r2, r3 = [], [], []
    for alpha in alphas:
        for beta in betas:
            random.setstate(state)
            uav_conf = []
            for u_i in range(uav_count):
                uav_conf.append(random.randint(0, n-1))
            victim_conf = []
            for v_j in range(victim_count):
                victim_conf.append(random.randint(0, n-1))
            trial_results = run_trial(alpha, beta, n, uav_conf, victim_conf,
                    adj, t, collisions=False, stay_put=False)
            r1.append(trial_results)
            trial_results = run_trial(alpha, beta, n, uav_conf, victim_conf,
                    adj, t, collisions=True, stay_put=False)
            r2.append(trial_results)
            trial_results = run_trial(alpha, beta, n, uav_conf, victim_conf,
                    adj, t, collisions=False, stay_put=True)
            r3.append(trial_results)
    return r1, r2, r3


def graph_results(r1, r2, r3, title):
    data = []
    for p_i in r1:
        data.append([p_i[0], p_i[1], p_i[2]])
    df = pd.DataFrame(data, columns=['X', 'Y', 'Z'])
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(df['Y'], df['X'], df['Z'], cmap=plt.cm.jet, linewidth=0.01)
    ax.set_title('Best Accrued Reward across values of Alpha and Beta')
    ax.set_ylabel('alpha (α)')
    ax.set_xlabel('beta (β)')
    ax.set_zlabel('accrued reward (R)')
    plt.show()
    plt.savefig(title + '.png')
    delta = []
    for i in range(len(r1)):
        t1, t2 = r1[i], r2[i]
        delta.append((t1[0], t1[1], t2[2]-t1[2]))
    data = []
    for d_i in delta:
        data.append([d_i[0], d_i[1], d_i[2]])
    df = pd.DataFrame(data, columns=['X', 'Y', 'Z'])
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(df['Y'], df['X'], df['Z'], cmap=plt.cm.jet, linewidth=0.01)
    ax.set_title('Differential Accrued Reward across values of Alpha and Beta')
    ax.set_ylabel('alpha (α)')
    ax.set_xlabel('beta (β)')
    ax.set_zlabel('accrued reward (R)')
    plt.show()
    plt.savefig(title + '.collisions.diff.png')
    delta = []
    for i in range(len(r1)):
        t1, t2 = r1[i], r3[i]
        delta.append((t1[0], t1[1], t2[2]-t1[2]))
    data = []
    for d_i in delta:
        data.append([d_i[0], d_i[1], d_i[2]])
    df = pd.DataFrame(data, columns=['X', 'Y', 'Z'])
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(df['Y'], df['X'], df['Z'], cmap=plt.cm.jet, linewidth=0.01)
    ax.set_title('Differential Accrued Reward across values of Alpha and Beta')
    ax.set_ylabel('alpha (α)')
    ax.set_xlabel('beta (β)')
    ax.set_zlabel('accrued reward (R)')
    plt.show()
    plt.savefig(title + '.stay.diff.png')
    plt.close('all')


def main():
    seed = 695480078
    random.seed(seed)
    state = random.getstate()
    uavs = [4, 8, 16, 24, 32, 64, 128]
    victims = 10
    n, rows, cols = 164, 4, 41
    turns = [15, 30, 45, 60, 120]
    adj = {}
    for i in range(n):
        adj_list = []
        if i // cols - 1 >= 0:
            adj_list.append( (i // cols - 1) * cols + i % cols )
        if (i + 1) % cols != 0:
            adj_list.append( i + 1 )
        if i // cols + 1 < rows:
            adj_list.append( (i // cols + 1) * cols + i % cols )
        if i % 41 != 0:
            adj_list.append( i - 1 )
        adj[i] = adj_list
    alphas = [ float(x+1) / 20.0 for x in range(20) ]
    betas = [ float(x+1) / 20.0 for x in range(20) ]
    for t in turns:
        for uav in uavs:
            r1, r2, r3 = run_trials(uav, victims, n, rows, cols, adj, alphas, betas, t, state)
            graph_results(r1, r2, r3, 'results-' + str(t) + '/fig.' + str(uav))


if __name__ == "__main__":
    main()
